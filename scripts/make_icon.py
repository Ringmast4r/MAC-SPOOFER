"""Render the existing house artwork into Windows icon frames."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
root = Path(__file__).resolve().parents[1]
sizes = [16,20,24,32,40,48,64,128,256]
for source, name in [('nw-globe-1024.png','app'),('shortcut-blade-master.png','shortcut-blade')]:
    im = Image.open(root/'assets'/source).convert('RGBA')
    frames=[]
    for n in sizes:
        frame=im.resize((n,n),Image.Resampling.LANCZOS)
        if n<=32: frame=frame.filter(ImageFilter.UnsharpMask(radius=.4,percent=110,threshold=2))
        frames.append(frame)
    im.save(root/'assets'/f'{name}.ico',format='ICO',sizes=[(n,n) for n in sizes],append_images=frames)
strip = Image.new('RGB',(1050,330),'#efefef')
draw = ImageDraw.Draw(strip)
for y,color in [(0,'#111111'),(165,'#ffffff')]:
    draw.rectangle((0,y,1050,y+165),fill=color)
    x = 14
    for n in sizes:
        icon = Image.open(root/'assets'/'shortcut-blade-master.png').convert('RGBA').resize((n,n),Image.Resampling.LANCZOS)
        if n<=32: icon=icon.filter(ImageFilter.UnsharpMask(radius=.4,percent=110,threshold=2))
        display = min(n,128)
        if n>128: icon=icon.resize((display,display),Image.Resampling.LANCZOS)
        strip.paste(icon,(x,y+10),icon)
        draw.text((x,y+143),str(n),fill='#aaaaaa' if y==0 else '#444444')
        x += display+35
strip.save(root/'build'/'icon-strip.png')
print('House artwork icons rendered.')
