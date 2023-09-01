import time
import datetime
import nidaqmx
import numpy as np

from tqdm import tqdm
from typing import Tuple

def medir(duracion: float, fs: int, device_name: str) -> np.ndarray:
    """
    Medir un canal de la DAQ.

    Parametros:
        - duracion (float): Cantidad de segundos a medir.
        - fs (int): Cantidad de puntos por segundo.
        - device_name (str): Nombre de la DAQ conectada. Obtenible mediante
                             "nidaqmx.system.System.local().devices[0].name"
    """

    cant_puntos = int(duracion*fs) # Tiempo a medir por cantidad de puntos por segundo

    # Configuraciones del canal de medicion
    terminal_config = nidaqmx.constants.TerminalConfiguration.RSE
    sample_mode = nidaqmx.constants.AcquisitionType.FINITE
    samples_per_channel = nidaqmx.constants.READ_ALL_AVAILABLE

    with nidaqmx.Task() as task:

        # Set voltage channel.
        task.ai_channels.add_ai_voltage_chan(f"{device_name}/ai1", 
                                             terminal_config = terminal_config, 
                                             max_val=10, 
                                             min_val=0)
        
        # Medir una cantidad de puntos.
        task.timing.cfg_samp_clk_timing(fs, 
                                        samps_per_chan=cant_puntos, 
                                        sample_mode=sample_mode)
        datos = task.read(number_of_samples_per_channel=samples_per_channel)           

    return np.asarray(datos)

def medir_continuo(duracion: float = 5, 
                   fs: int = 300000, 
                   max_iter: int = 10) -> Tuple[np.ndarray]:

    device_name = nidaqmx.system.System.local().devices[0].name

    tiempos, datos_y = [], []
    try:
        for i in tqdm(range(max_iter)):

            t_0 = time.perf_counter()

            y = medir(duracion, fs, device_name)
            
            datos_y = np.concatenate([datos_y, y])

            tiempos.append(time.perf_counter()-t_0)

            time.sleep(1)
    except KeyboardInterrupt:
        print("Deteniendo")
    return tiempos, datos_y

def save_file(datos_y: np.ndarray) -> None:

    muestra = input("Nombre de la muestra: ")
    date = datetime.datetime.now().strftime("%m-%d-%Y %H %M")
    file = f"{muestra} {date}.npz"

    np.savez_compressed(file, y=datos_y)