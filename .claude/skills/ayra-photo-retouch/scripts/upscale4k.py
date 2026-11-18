#!/usr/bin/env python3
"""Ekran görüntüsü / video kadrını keyfiyyətli böyüt (Real-ESRGAN x4plus, CPU, plitə ilə).
Üz bərpası (GFPGAN/CodeFormer) YOXDUR — üz cizgiləri dəyişdirilmir.
  python3 upscale4k.py giriş.png çıxış.png [--crop x0,y0,x1,y1] [--size 2160x3840]
--crop koordinatları giriş şəklinin piksellərindədir. Model ilk dəfə ~/.cache/ayra-sr/ qovluğuna yüklənir.
"""
import argparse, os, urllib.request
import numpy as np, torch
from PIL import Image, ImageFilter
import torch.nn as nn, torch.nn.functional as Fn
class RDB(nn.Module):
    def __init__(s,nf=64,gc=32):
        super().__init__()
        s.conv1=nn.Conv2d(nf,gc,3,1,1); s.conv2=nn.Conv2d(nf+gc,gc,3,1,1); s.conv3=nn.Conv2d(nf+2*gc,gc,3,1,1)
        s.conv4=nn.Conv2d(nf+3*gc,gc,3,1,1); s.conv5=nn.Conv2d(nf+4*gc,nf,3,1,1); s.l=nn.LeakyReLU(0.2,True)
    def forward(s,x):
        x1=s.l(s.conv1(x)); x2=s.l(s.conv2(torch.cat((x,x1),1))); x3=s.l(s.conv3(torch.cat((x,x1,x2),1)))
        x4=s.l(s.conv4(torch.cat((x,x1,x2,x3),1))); x5=s.conv5(torch.cat((x,x1,x2,x3,x4),1)); return x5*0.2+x
class RRDB(nn.Module):
    def __init__(s,nf=64):
        super().__init__(); s.rdb1=RDB(nf); s.rdb2=RDB(nf); s.rdb3=RDB(nf)
    def forward(s,x): return s.rdb3(s.rdb2(s.rdb1(x)))*0.2+x
class RRDBNet(nn.Module):
    def __init__(s,nf=64,nb=23):
        super().__init__()
        s.conv_first=nn.Conv2d(3,nf,3,1,1); s.body=nn.Sequential(*[RRDB(nf) for _ in range(nb)]); s.conv_body=nn.Conv2d(nf,nf,3,1,1)
        s.conv_up1=nn.Conv2d(nf,nf,3,1,1); s.conv_up2=nn.Conv2d(nf,nf,3,1,1); s.conv_hr=nn.Conv2d(nf,nf,3,1,1); s.conv_last=nn.Conv2d(nf,3,3,1,1); s.l=nn.LeakyReLU(0.2,True)
    def forward(s,x):
        f=s.conv_first(x); f=f+s.conv_body(s.body(f))
        f=s.l(s.conv_up1(Fn.interpolate(f,scale_factor=2,mode='nearest'))); f=s.l(s.conv_up2(Fn.interpolate(f,scale_factor=2,mode='nearest')))
        return s.conv_last(s.l(s.conv_hr(f)))
URL='https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth'
ap=argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('dst')
ap.add_argument('--crop'); ap.add_argument('--size',default='2160x3840'); ap.add_argument('--tile',type=int,default=192)
a=ap.parse_args()
W=os.path.expanduser('~/.cache/ayra-sr/RealESRGAN_x4plus.pth'); os.makedirs(os.path.dirname(W),exist_ok=True)
if not os.path.exists(W): urllib.request.urlretrieve(URL,W)
torch.set_num_threads(os.cpu_count() or 4)
m=RRDBNet(); sd=torch.load(W,map_location='cpu'); m.load_state_dict(sd.get('params_ema',sd.get('params',sd))); m.eval()
im=Image.open(a.src).convert('RGB')
if a.crop: im=im.crop(tuple(int(v) for v in a.crop.split(',')))
x=torch.from_numpy(np.asarray(im).astype(np.float32)/255).permute(2,0,1)[None]
_,_,H,Wd=x.shape; t=a.tile; p=12; out=torch.zeros(1,3,H*4,Wd*4)
with torch.no_grad():
    for y0 in range(0,H,t):
        for x0 in range(0,Wd,t):
            ya,yb=max(0,y0-p),min(H,y0+t+p); xa,xb=max(0,x0-p),min(Wd,x0+t+p)
            o=m(x[:,:,ya:yb,xa:xb])
            oy,ox=(y0-ya)*4,(x0-xa)*4; h=min(t,H-y0)*4; w=min(t,Wd-x0)*4
            out[:,:,y0*4:y0*4+h,x0*4:x0*4+w]=o[:,:,oy:oy+h,ox:ox+w]
r=Image.fromarray((out[0].clamp(0,1).permute(1,2,0).numpy()*255).round().astype(np.uint8))
tw,th=(int(v) for v in a.size.split('x'))
# kəsimi hədəf nisbətinə uyğunlaşdır (mərkəzdən), sonra ölçü
sr=tw/th; rw,rh=r.size
if rw/rh>sr: nw=int(rh*sr); r=r.crop(((rw-nw)//2,0,(rw-nw)//2+nw,rh))
elif rw/rh<sr: nh=int(rw/sr); r=r.crop((0,(rh-nh)//2,rw,(rh-nh)//2+nh))
r=r.resize((tw,th),Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.2,percent=40,threshold=2))
r.save(a.dst); print(a.dst, r.size)
