# DeepFilterNet ilə fon səsinin təmizlənməsi (danışanın səsi saxlanılır).  python3 mu/dfn.py giriş.wav çıxış.wav [atten_dB]
import sys,types,numpy as np,torch
m=types.ModuleType("torchaudio.backend"); c=types.ModuleType("torchaudio.backend.common"); c.AudioMetaData=type("AudioMetaData",(),{}); sys.modules["torchaudio.backend"]=m; sys.modules["torchaudio.backend.common"]=c
from df.enhance import enhance, init_df
from scipy.io import wavfile
model,st,_=init_df(log_level="ERROR")
sr,x=wavfile.read(sys.argv[1]); assert sr==st.sr(),(sr,st.sr()); x=x.astype(np.float32)/32768
if x.ndim>1: x=x.mean(1)
att=float(sys.argv[3]) if len(sys.argv)>3 else None
y=enhance(model,st,torch.from_numpy(x)[None],atten_lim_db=att)[0].numpy()
wavfile.write(sys.argv[2],sr,(np.clip(y,-1,1)*32767).astype(np.int16)); print("ok",len(y)/sr)
