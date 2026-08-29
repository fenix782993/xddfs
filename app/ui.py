from PIL import Image,ImageDraw,ImageFont
from io import BytesIO
from aiogram.types import BufferedInputFile
def font(s):
    try:return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",s)
    except:return ImageFont.load_default()
def visual(title,subtitle,icon="🔥"):
    im=Image.new("RGB",(1280,720),(8,9,15));d=ImageDraw.Draw(im)
    d.rounded_rectangle((30,30,1250,690),35,outline=(190,30,55),width=5)
    d.text((80,90),icon,font=font(82),fill="white");d.text((205,105),title,font=font(54),fill="white")
    d.multiline_text((90,230),subtitle,font=font(30),fill=(205,205,215),spacing=14)
    d.text((90,620),"FENIX COIN • PLAY • RISE",font=font(25),fill=(235,235,240))
    b=BytesIO();im.save(b,"PNG");b.seek(0)
    return BufferedInputFile(b.read(),filename="fenix.png")
