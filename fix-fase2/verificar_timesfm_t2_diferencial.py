"""T2 — Test diferencial anti-contaminacion (bug PEFT in-place del spike).

El spike aplico PeftModel.from_pretrained(base, adapter) SOBRE la misma
instancia que luego uso para predecir "base" — por eso zeroshot==lora_ft en
resultado_timesfm_lora.json (bug fisico, confirmado en Fase 0).

Aqui base y base+adapter corren en PROCESOS INDEPENDIENTES (la tarea pide
"proceso independiente o del + gc"); cada uno carga su propio
from_pretrained, predice las mismas 3 ventanas sinteticas y guarda el .npy
en disco. El proceso ft ademas entrena el adapter 2 steps (2 ventanas,
seed 42) para que lora_B != 0 — con B=0 recien inicializado el adapter no
tiene efecto por construccion y el test seria trivial. Criterio: rel_diff > 1e-3.

Uso (venv del spike, desde la raiz de la copia):
  python verificar_timesfm_t2_diferencial.py            # orquesta todo
  python verificar_timesfm_t2_diferencial.py base       # solo proceso base
  python verificar_timesfm_t2_diferencial.py ft         # solo proceso ft
"""
import gc
import os
import subprocess
import sys
import time

import numpy as np
import torch

sys.path.insert(0, "src")
from timesfm_harness import serie_sintetica, CTX, H, SEED

MODEL_ID = "google/timesfm-2.5-200m-transformers"
LORA_R = 4
LORA_ALPHA = 8
LORA_DROPOUT = 0.05
LR = 1e-3   # lr del TEST diferencial (no el del protocolo §4): solo necesitamos que lora_B se mueva lo bastante para medir aplicacion
TMP = "/tmp/timesfm_t2"


def datos():
    series = [serie_sintetica(CTX + 400, 0.003, 0.01, seed=SEED + k)
              for k in range(4)]
    ventanas = [(series[k], CTX + k * 37) for k in range(3)]
    return series, ventanas


def cargar():
    from transformers import TimesFm2_5ModelForPrediction
    m = TimesFm2_5ModelForPrediction.from_pretrained(
        MODEL_ID, torch_dtype=torch.float32, device_map="cpu")
    m.eval()
    return m


def predecir(model, ventanas):
    out = []
    with torch.no_grad():
        for s, start in ventanas:
            ctx = torch.tensor(s[start:start + CTX], dtype=torch.float32,
                               device="cpu").unsqueeze(0)
            p = model(past_values=ctx).mean_predictions[0, :H]
            out.append(p.float().cpu().numpy())
    return np.array(out)


def proceso_base():
    _, ventanas = datos()
    model = cargar()
    np.save(TMP + "_base.npy", predecir(model, ventanas))


def proceso_ft():
    series, ventanas = datos()
    from peft import LoraConfig, get_peft_model
    ft = cargar()
    ft = get_peft_model(ft, LoraConfig(
        r=LORA_R, lora_alpha=LORA_ALPHA, lora_dropout=LORA_DROPOUT,
        target_modules="all-linear", bias="none"))
    opt = torch.optim.AdamW([p for p in ft.parameters() if p.requires_grad],
                            lr=LR, weight_decay=0.01)
    torch.manual_seed(SEED)
    CTX_TRAIN = 64    # contexto minimo: el test solo exige lora_B != 0;
                      # el forward del modelo reserva ~4.1 GB de golpe (diag
                      # 2026-10-13) y el VPS tiene ~5 GB disponibles
    for s in series[:3]:                  # 3 steps: el pool de memoria de
                                          # PyTorch no libera entre forwards;
                                          # con ~5 GB disponibles, 3 es el max
                                          # observado sin OOM en este VPS
        ctx = torch.tensor(s[-CTX_TRAIN - H:-H], dtype=torch.float32,
                           device="cpu").unsqueeze(0)
        tgt = torch.tensor(s[-H:], dtype=torch.float32,
                           device="cpu").unsqueeze(0)
        out = ft(past_values=ctx, future_values=tgt)
        out.loss.backward()
        opt.step()
        opt.zero_grad()
    ft.eval()
    np.save(TMP + "_ft.npy", predecir(ft, ventanas))


def main():
    t0 = time.time()
    venv = "/root/.openclaw/workspace/timesfm-spike/venv/bin/python"
    script = os.path.abspath(__file__)
    os.makedirs(TMP.split("/timesfm_t2")[0], exist_ok=True)
    for modo, log in (("base", "/tmp/t2_base.log"), ("ft", "/tmp/t2_ft.log")):
        with open(log, "w") as lf:
            r = subprocess.run([venv, "-u", script, modo],
                               stdout=lf, stderr=subprocess.STDOUT)
        if r.returncode != 0:
            print(f"proceso {modo} fallo (exit {r.returncode}):")
            print(open(log).read()[-1500:])
            return 1
        print(f"proceso {modo} OK [{time.time() - t0:.0f}s]")

    p_base = np.load(TMP + "_base.npy")
    p_ft = np.load(TMP + "_ft.npy")
    rel = float(np.abs(p_ft - p_base).mean() / (np.abs(p_base).mean() + 1e-12))
    print(f"predicciones base : {p_base[0][:4].round(2)}")
    print(f"predicciones +lora: {p_ft[0][:4].round(2)}")
    print(f"rel_diff = {rel:.6f} (umbral > 1e-3)  [{time.time() - t0:.0f}s]")
    if rel > 1e-3:
        print("T2 OK: base y base+adapter difieren en procesos separados — "
              "el adapter se aplica de verdad (el bug del spike esta cerrado).")
        return 0
    print("T2 FALLO: instancias identicas — el adapter no se aplica. NO correr datos reales.")
    return 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "base":
        proceso_base()
    elif len(sys.argv) > 1 and sys.argv[1] == "ft":
        proceso_ft()
    else:
        sys.exit(main())
