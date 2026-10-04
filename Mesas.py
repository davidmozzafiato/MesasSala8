import subprocess
import sys

try:
    import matplotlib
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
    import matplotlib

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Configuración de la página web
st.set_page_config(page_title="Reacomodo Sala 8", layout="centered")

MESA_W, MESA_H = 0.9, 0.5

# 1. ESTADO INICIAL
bloques_iniciales = {
    'par_1': (2.0, 7.5, 'H', 'D', '9, 10'),    'par_2': (7.0, 8.0, 'H', 'D', '12, 11'),
    'par_3': (2.0, 6.0, 'H', 'D', '1, 2'),     'par_4': (7.0, 6.0, 'H', 'D', '13, 14'),
    'par_5': (2.0, 4.5, 'H', 'D', '15, 16'),   'par_6': (7.0, 4.5, 'H', 'D', '5, 6'),
    'par_7': (2.0, 1.8, 'H', 'D', '8, 7'),     'par_8': (7.0, 1.8, 'H', 'D', '4, 3')
}

# 2. ESTADO FINAL OBJETIVO
bloques_objetivo = {
    'par_5': (2.0, 8.0, 'H', 'D', '16, 15'),   'par_2': (7.0, 8.0, 'H', 'D', '12, 11'),
    'par_4': (2.0, 6.8, 'H', 'U', '14, 13'),   'par_1': (7.0, 6.8, 'H', 'U', '10, 9'),
    'par_6': (1.0, 4.5, 'V', 'L', '6, 5'),     'par_3': (8.0, 4.5, 'V', 'R', '2, 1'),
    'par_7': (1.0, 1.8, 'V', 'L', '7, 8'),     'par_8': (8.0, 1.8, 'V', 'R', '3, 4')
}

# 3. GENERADOR DE PASOS
@st.cache_data
def generar_pasos():
    pasos = [(dict(bloques_iniciales), "Estado Inicial de la Sala 8")]

    def mover_par_seguro(estado_prev, clave_par, pos_fin):
        x_i, y_i, o_i, d_i, tag_i = estado_prev[clave_par]
        x_f, y_f, o_f, d_f, tag_f = pos_fin
        
        etiqueta_transf = f"[{tag_i}] → [{tag_f}]" if tag_i != tag_f else f"[{tag_i}]"
            
        if abs(x_i - x_f) < 0.2 and abs(y_i - y_f) < 0.2:
            if (o_i, d_i, tag_i) != (o_f, d_f, tag_f):
                nuevo = dict(estado_prev)
                nuevo[clave_par] = (x_f, y_f, o_f, d_f, tag_f)
                return [(nuevo, f"Rotando in-situ Bloque {etiqueta_transf}")]
            return []
        
        sub_pasos = [
            ((4.5, y_i, o_i, d_i, tag_i), f"Moviendo Bloque {etiqueta_transf} → Entrando al pasillo central"),
            ((4.5, y_f, o_i, d_i, tag_i), f"Moviendo Bloque {etiqueta_transf} → Traslado vertical por el pasillo"),
            ((x_f, y_f, o_f, d_f, tag_f), f"Moviendo Bloque {etiqueta_transf} → Acomodado en posición final")
        ]
        
        fotogramas = []
        temp = dict(estado_prev)
        for pos_sub, txt_sub in sub_pasos:
            temp[clave_par] = pos_sub
            fotogramas.append((dict(temp), txt_sub))
        return fotogramas

    secuencia_pares = [
        ('par_1', bloques_objetivo['par_1']),
        ('par_5', bloques_objetivo['par_5']),
        ('par_4', bloques_objetivo['par_4']),
        ('par_6', bloques_objetivo['par_6']),
        ('par_3', bloques_objetivo['par_3']),
        ('par_7', bloques_objetivo['par_7']),
        ('par_8', bloques_objetivo['par_8'])
    ]

    for clave_p, pos_dest in secuencia_pares:
        ult_estado, _ = pasos[-1]
        pasos_generados = mover_par_seguro(ult_estado, clave_p, pos_dest)
        if pasos_generados:
            pasos.extend(pasos_generados)
            
    return pasos

pasos_bloques = generar_pasos()

# 4. CONTROL DE ESTADO DE NAVEGACIÓN EN STREAMLIT
if 'paso_actual' not in st.session_state:
    st.session_state.paso_actual = 0

def dibujar_paso(paso):
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 9.5)
    ax.set_xticks(range(10))
    ax.set_yticks(range(10))
    ax.grid(True, which='both', color='gray', linestyle=':', linewidth=0.5)
    
    # Paredes y Puerta
    ax.plot([0.5, 8.5], [9, 9], color='black', linewidth=4)
    ax.plot([0.5, 0.5], [0.5, 9], color='black', linewidth=4)
    ax.plot([8.5, 8.5], [2, 9], color='black', linewidth=4)
    ax.plot([5.5, 8.5], [0.5, 0.5], color='red', linewidth=6, label='Puerta')
    
    estado, accion_texto = pasos_bloques[paso]
    
    for clave_par, (x, y, orient, dir_frente, etiqueta) in estado.items():
        if orient == 'H':
            w, h = MESA_W * 2 + 0.2, MESA_H
            texto = f'Bloque [{etiqueta}]'
            rot = 0
            font_size = 8.5
        else:
            w, h = MESA_H, MESA_W * 2 + 0.2
            texto = f'Bloque [{etiqueta}]'
            rot = 90 if x < 4.5 else -90
            font_size = 8.0
            
        color = '#2ecc71' if orient == 'V' or (dir_frente == 'U' and y > 6.0) or (dir_frente == 'D' and y > 7.5) else '#e67e22'
        
        rect = patches.Rectangle((x - w/2, y - h/2), w, h,
                                 linewidth=1.8, edgecolor='black', facecolor=color)
        ax.add_patch(rect)
        
        frente_w, frente_h = w, h
        fx, fy = x - w/2, y - h/2
        
        if dir_frente == 'D':
            fy, frente_h = y - h/2, 0.1
        elif dir_frente == 'U':
            fy, frente_h = y + h/2 - 0.1, 0.1
        elif dir_frente == 'L':
            fx, frente_w = x - w/2, 0.1
        elif dir_frente == 'R':
            fx, frente_w = x + w/2 - 0.1, 0.1
            
        frente_rect = patches.Rectangle((fx, fy), frente_w, frente_h,
                                        linewidth=0, facecolor='#3498db', zorder=3)
        ax.add_patch(frente_rect)
        
        ax.text(
            x, y, texto,
            ha='center', va='center',
            rotation=rot,
            fontweight='bold',
            color='white',
            fontsize=font_size,
            zorder=4
        )
        
    ax.set_title(f'Paso {paso} / {len(pasos_bloques)-1}\n{accion_texto}', 
                 fontsize=11, fontweight='bold', color='#1a252f', pad=10)
    return fig

# 5. INTERFAZ WEB
st.title("Simulador de Reacomodo - Sala 8")

fig = dibujar_paso(st.session_state.paso_actual)
st.pyplot(fig)

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if st.button("<< Anterior", use_container_width=True):
        if st.session_state.paso_actual > 0:
            st.session_state.paso_actual -= 1
            st.rerun()

with col3:
    if st.button("Siguiente >>", use_container_width=True):
        if st.session_state.paso_actual < len(pasos_bloques) - 1:
            st.session_state.paso_actual += 1
            st.rerun()