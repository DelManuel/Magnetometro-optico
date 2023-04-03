import numpy as np
import matplotlib.pyplot as plt
np.set_printoptions(threshold=8)

def set_osc_acq(osc):
    # Configuración de la adquisición de curvas
    osc.write('DAT:ENC RPB')
    osc.write('DAT:WID 1')
    osc.write('DAT:STAR 1')
    osc.write('DAT:STOP 2500')
    osc.write('ACQ:MOD SAMP')

def parse_parameters(wfmp_params):
    """Parsea la información de configuración de las escalas y las almacena en un diccionario.
    Para después simplificar el gráfico de la curva."""
    result = {}
    header_def = [('BYT_Nr', int),
              ('BiT_Nr', int),
              ('ENCdg', str),
              ('BN_Fmt', str),
              ('BYT_Or', str)]
    wfrm1_def = [('WFID', str),
             ('NR_PT', int),
             ('PT_FMT', str),
             ('XUNIT', str),
             ('XINCR', float),
             ('PT_Off', int),
             ('YUNIT', str),
             ('YMULT', float),
             ('YOFf', float),
             ('YZEro', float)]

    full_def = header_def + [(f'wfm1:{k}', c) for k, c in wfrm1_def] \
           + [(f'wfm2:{k}', c) for k, c in wfrm1_def] \
           + [(f'wfm3:{k}', c) for k, c in wfrm1_def] \
           + [(f'wfm4:{k}', c) for k, c in wfrm1_def]
    for (key, conversor), param in zip(full_def, wfmp_params.split(';')):
        result[key] = conversor(param)
    return result

def escalar_curva(data, parametros):
    """Devuelve el par de vectores (t, v) a partir de la curva levantada del osciloscopio
    y los parámetros de escala del mismo. El eje temporal está en ms y el vertical en Volts/"""
    n = len(data)
    t = 1e3 * (np.arange(n) - parametros['wfm1:PT_Off']) * parametros['wfm1:XINCR']

    v = (data - parametros['wfm1:YOFf']) * parametros['wfm1:YMULT'] \
                    + parametros['wfm1:YZEro']
    return t, v


import pyvisa as visa
rm = visa.ResourceManager()
rm.list_resources() # Qué recursos hay disponibles?

# Abrimos el recurso de VISA, en este caso es un osciloscopio
osc = rm.open_resource('GPIB0::7::INSTR')
osc.query('*IDN?') # Este comando está dispobible en TODOS los dispositivos

# Probamos otro queries que dependen del disposivo `query`
osc.query('CH1?')
osc.query('HOR?')

set_osc_acq(osc)

osc.write('DAT:SOU CH1') # Adquirimos del canal 1
# La lectura se puede hacer en modo binario, lo que la hace más eficiente
conf_parameters_a = parse_parameters(osc.query('WFMP?'))
data_a = osc.query_binary_values('CURV?', datatype='B', container=np.array)
data_a

# Cambiamos la escala temporal y volvemos a adquirir
scale = '250e-6'
osc.write(f'HOR:SCA {scale}')
conf_parameters_b = parse_parameters(osc.query('WFMP?'))
data_b = osc.query_binary_values('CURV?', datatype='B', container=np.array)
data_b



plt.rcParams['font.size'] = '16'
t_a, v_a = escalar_curva(data_a, conf_parameters_a)
t_b, v_b = escalar_curva(data_b, conf_parameters_b)

fig, (ax1, ax2) = plt.subplots(1,2, figsize=(14,6))
ax1.plot(t_a, v_a)
ax1.set_xlabel('t [ms]')
ax1.set_ylabel('V_CH1 [V]')
ax1.set_title('Base de tiempo 100us')
ax2.plot(t_b, v_b)
ax2.set_xlabel('t [ms]')
ax2.set_ylabel('V_CH1 [V]')
ax2.set_title('Base de tiempo 250us')
plt.show()