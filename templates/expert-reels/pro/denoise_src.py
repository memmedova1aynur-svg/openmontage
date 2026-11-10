"""Mənbə videonun səsini fon küyündən təmizləyir (noisereduce, stationary, yumşaq maska) və videonu kopyalayaraq yenidən birləşdirir.
İstifadə: python3 denoise_src.py <layihə/media/originals/fayl.mov> [prop=0.9]. Orijinal .orig kimi saxlanılır.
afftdn/anlmdn istifadə etmə: səsi boğur."""
import sys,subprocess,os,numpy as np,wave,noisereduce as nr,shutil
src=sys.argv[1]; bak=src+'.orig'
if not os.path.exists(bak): shutil.copy(src,bak); os.chmod(src,0o644)
subprocess.run(['ffmpeg','-v','error','-i',bak,'-vn','-ac','1','-ar','48000','-y','/tmp/_a.wav'],check=True)
w=wave.open('/tmp/_a.wav');sr=w.getframerate();x=np.frombuffer(w.readframes(w.getnframes()),np.int16)/32768
n=sr//10;F=x[:len(x)//n*n].reshape(-1,n);r=np.sqrt((F**2).mean(1));q=np.argsort(r)[:max(10,len(r)//12)]
noise=np.concatenate([F[i] for i in sorted(q)])
z=nr.reduce_noise(y=x,sr=sr,y_noise=noise,stationary=True,prop_decrease=float(sys.argv[2]) if len(sys.argv)>2 else 0.9,freq_mask_smooth_hz=250,time_mask_smooth_ms=60,n_fft=2048)
z=z/np.max(np.abs(z))*0.9
o=wave.open('/tmp/_b.wav','wb');o.setnchannels(1);o.setsampwidth(2);o.setframerate(sr);o.writeframes((z*32767).astype(np.int16).tobytes());o.close()
subprocess.run(['ffmpeg','-v','error','-i',bak,'-i','/tmp/_b.wav','-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','256k','-ac','2','-y',src+'.tmp.mov'],check=True)
os.replace(src+'.tmp.mov',src)
def m(y):
    F=y[:len(y)//n*n].reshape(-1,n);rr=20*np.log10(np.sqrt((F**2).mean(1))+1e-9);sp=rr>np.percentile(rr,60)
    S=np.abs(np.fft.rfft(F*np.hanning(n),axis=1));fq=np.fft.rfftfreq(n,1/sr)
    return round(20*np.log10(S[sp][:,(fq>3000)&(fq<8000)].mean()/S[sp][:,(fq>200)&(fq<1000)].mean()),1),round(np.percentile(rr,10)-np.percentile(rr,90),1)
print('src HF,quiet-vs-loud',m(x),'dn',m(z))
