import numpy as np,wave
SR=48000;rng=np.random.default_rng(7)
def save(n,x,peak=0.9):
    if x.ndim==1:x=np.stack([x,x],1)
    x=x/np.max(np.abs(x))*peak;d=(x*32767).astype(np.int16)
    with wave.open(f'{n}.wav','wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(d.tobytes())
def bp(x,lo,hi):
    X=np.fft.rfft(x);f=np.fft.rfftfreq(len(x),1/SR);X[(f<lo)|(f>hi)]=0;return np.fft.irfft(X,len(x))
def lp_sweep(x,f0,f1):
    out=np.zeros_like(x);seg=2048;n=len(x)
    for i in range(0,n,seg//2):
        c=f0*(f1/f0)**(i/n);b=x[i:i+seg]
        if len(b)<seg:b=np.pad(b,(0,seg-len(b)))
        y=bp(b*np.hanning(seg),20,c);j=min(seg,n-i);out[i:i+j]+=y[:j]
    return out
t=lambda d:np.arange(int(SR*d))/SR
# 1 kinematik zərbə (boom): sub + küy quyruğu
T=t(1.6);sub=np.sin(2*np.pi*(48+30*np.exp(-T/0.08))*T)*np.exp(-T/0.35)
nz=lp_sweep(rng.normal(0,1,len(T)),2500,120)*np.exp(-T/0.25)*0.5
save('c_boom',np.tanh(1.6*(sub+nz)))
# 2 havalı keçid (whoosh) — stereo sürüşmə
T=t(0.55);u=T/T[-1];x=lp_sweep(rng.normal(0,1,len(T)),400,6000)*np.sin(np.pi*u)**2
save('c_whoosh',np.stack([x*(1.2-u),x*(0.2+u)],1))
# 3 lampa kliki (açılma) + yüngül uğultu
T=t(0.5);c1=bp(rng.normal(0,1,len(T)),1500,9000)*np.exp(-T/0.004);T2=T-0.035;c2=np.where(T2>0,bp(rng.normal(0,1,len(T)),800,6000)*np.exp(-np.clip(T2,0,None)/0.006),0)
hum=0.04*np.sin(2*np.pi*100*T)*np.clip((T-0.04)/0.05,0,1)*np.exp(-T/0.25)
save('c_lamp',c1+0.7*c2+hum,0.8)
# 4 riser (küy, tonsuz)
T=t(1.2);u=T/T[-1];x=lp_sweep(rng.normal(0,1,len(T)),300,8000)*u**2.2*(1-np.exp(-(1-u)*60))
save('c_riser',x,0.7)
# 5 kağız / foto düşməsi
T=t(0.35);u=T/T[-1];x=bp(rng.normal(0,1,len(T)),1500,9000)*(0.5+0.5*np.abs(np.sin(2*np.pi*30*T)))*np.sin(np.pi*u)**1.2;thud=np.sin(2*np.pi*90*T)*np.exp(-T/0.03)*0.6
save('c_paper',x+thud,0.7)
# 6 söz kliki (yazı)
T=t(0.18);x=bp(rng.normal(0,1,len(T)),2000,9000)*np.exp(-T/0.006)+0.4*np.sin(2*np.pi*1800*T)*np.exp(-T/0.01)
save('c_tick',x,0.55)
# 7 tərs swell (vurğudan əvvəl)
T=t(0.7);u=T/T[-1];x=bp(rng.normal(0,1,len(T)),200,5000)*u**3
save('c_swell',x,0.6)
print('ok')
