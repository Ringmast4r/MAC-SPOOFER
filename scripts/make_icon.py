"""Render the existing house artwork into Windows icon frames."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps
root = Path(__file__).resolve().parents[1]
sizes = [16,20,24,32,40,48,64,96,128,256]
# Preserve the gallery blade, replacing only the connected exterior background.
blade = Image.open(root/'assets'/'shortcut-blade-original-1024.jpg').convert('RGBA')
regions = ImageOps.grayscale(blade).point(lambda value: 255 if value >= 120 else 0)
ImageDraw.floodfill(regions, (blade.width//2,blade.height//16), 128)
outside = regions.point(lambda value: 255 if value == 128 else 0)
# Include the outer antialiased edge, which otherwise leaves a dark keying fringe.
outside = outside.filter(ImageFilter.MaxFilter(3))
blade.paste((255,255,255,255), (0,0), outside)
alpha = Image.new('L', blade.size, 0)
ImageDraw.Draw(alpha).rounded_rectangle((0,0,blade.width-1,blade.height-1), radius=int(blade.width*.24), fill=255)
blade.putalpha(alpha)
blade.save(root/'assets'/'shortcut-blade-white-master.png')
for source, name in [('nw-globe-1024.png','app'),('shortcut-blade-white-master.png','shortcut-blade-white')]:
    im = Image.open(root/'assets'/source).convert('RGBA')
    icon_sizes = sizes if name != 'app' else [n for n in sizes if n != 96]
    frames=[]
    for n in icon_sizes:
        frame=im.resize((n,n),Image.Resampling.LANCZOS)
        if n<=32: frame=frame.filter(ImageFilter.UnsharpMask(radius=.4,percent=110,threshold=2))
        frames.append(frame)
    im.save(root/'assets'/f'{name}.ico',format='ICO',sizes=[(n,n) for n in icon_sizes],append_images=frames)
# Existing 1.6.0 EXEs use this external path for their tray on the next launch.
(root/'assets'/'shortcut-blade.ico').write_bytes((root/'assets'/'shortcut-blade-white.ico').read_bytes())
strip = Image.new('RGB',(1050,330),'#efefef')
draw = ImageDraw.Draw(strip)
for y,color in [(0,'#111111'),(165,'#ffffff')]:
    draw.rectangle((0,y,1050,y+165),fill=color)
    x = 14
    for n in sizes:
        icon = Image.open(root/'assets'/'shortcut-blade-white-master.png').convert('RGBA').resize((n,n),Image.Resampling.LANCZOS)
        if n<=32: icon=icon.filter(ImageFilter.UnsharpMask(radius=.4,percent=110,threshold=2))
        display = min(n,128)
        if n>128: icon=icon.resize((display,display),Image.Resampling.LANCZOS)
        strip.paste(icon,(x,y+10),icon)
        draw.text((x,y+143),str(n),fill='#aaaaaa' if y==0 else '#444444')
        x += display+35
strip.save(root/'build'/'icon-strip.png')
print('House artwork icons rendered.')
