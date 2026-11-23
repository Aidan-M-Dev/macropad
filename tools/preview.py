"""Headless, depth-buffered previews of OpenSCAD's actual STL output (no OpenGL)."""
from paths import BUILD, GENERATED
import re,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageFilter,ImageDraw,ImageFont
from appearance import load_config,sync_scad,artwork_canvas,export_print_pack

def load(path):
 # OpenSCAD's default ASCII STL.
 vs=np.array(re.findall(r'vertex\s+([-+\deE.]+)\s+([-+\deE.]+)\s+([-+\deE.]+)',path.read_text()),dtype=float)
 return vs.reshape(-1,3,3)

def validate(path):
 tri=load(path); vertices,idx=np.unique(np.round(tri.reshape(-1,3),5),axis=0,return_inverse=True);idx=idx.reshape(-1,3)
 ed=np.concatenate([idx[:,[0,1]],idx[:,[1,2]],idx[:,[2,0]]]); _,cnt=np.unique(np.sort(ed,axis=1),axis=0,return_counts=True)
 # Connected face/vertex graph: separate components would mean loose, unprintable pieces.
 parents=np.arange(len(vertices))
 def root(i):
  while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
  return i
 for a,b in ed:
  a,b=root(a),root(b)
  if a!=b:parents[b]=a
 components=len({root(i) for i in range(len(vertices))})
 vol=np.sum(np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])))/6
 result={'file':path.name,'triangles':len(tri),'closed_edge_manifold':bool(np.all(cnt==2)),'connected_components':components,'volume_mm3':round(float(vol),2),'bounds_mm':np.round([vertices.min(0),vertices.max(0)],3).tolist()}
 assert result['closed_edge_manifold'] and components==1 and vol>0,result
 return result

# Surface opacity is an illustrative single-surface blend, not optical resin simulation.
bg=np.array([18,25,35],dtype=np.float32);W,H=1600,1200
refs=BUILD/'previews/meshes/m3x6'
log=(BUILD/'exports/logs/m3x6-base-m3x6.log').read_text()
dimensions=json.loads(re.search(r'case_size = (\[[^\]]+\])',log).group(1))
case_height=dimensions[2]
print_dims=json.loads(re.search(r'print_dimensions = (\[[^\]]+\])',log).group(1))
CFG=load_config(require_images=False);sync_scad(CFG)
CENTRES=np.array(json.loads((GENERATED/'pcb_geometry.json').read_text())['key_centres'])

def item(name,mesh,rgb,opacity=1,shift=0,texture=None,uv=None,frosted_blur_px=0,layer_height_mm=0,layer_line_strength=0):
    mesh=mesh.astype(float,copy=True);mesh[:,:,2]+=shift
    return dict(name=name,mesh=mesh,rgb=np.array(rgb),opacity=opacity,texture=texture,uv=uv,frosted_blur_px=frosted_blur_px,layer_height_mm=layer_height_mm,layer_line_strength=layer_line_strength)

def key_meshes_and_faces(refdir=refs):
    triangles=load(refdir/'keycaps.stl')
    groups=np.argmin(np.sum((triangles.mean(1)[:,None,:2]-CENTRES[None,:,:])**2,axis=2),axis=1)
    meshes=[];faces=[]
    for i,centre in enumerate(CENTRES):
        mesh=triangles[groups==i];z=mesh[:,:,2].max();v=mesh.reshape(-1,3)
        top=v[np.isclose(v[:,2],z)];width=float(np.ptp(top[:,0]))
        meshes.append(mesh);faces.append({'key':f'SW{i+1}','width_mm':width,'z':float(z),'centre':centre.tolist()})
    return meshes,faces

KEY_MESHES,FACES=key_meshes_and_faces()

def finish(material):
    return {name:material.get(name,0) for name in ['frosted_blur_px','layer_height_mm','layer_line_strength']}

def silkscreen_texture():
    px=40;im=Image.new('RGBA',(70*px,60*px));draw=ImageDraw.Draw(im)
    def point(p):return (p[0]*px,(60-p[1])*px)
    for primitive in json.loads((GENERATED/'pcb_silkscreen.json').read_text()):
        typ=primitive['type'];width=max(1,round(primitive.get('width',.15)*px));colour=(235,239,218,255)
        if typ=='text':
            font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',max(1,round(primitive['height']*px)))
            text=primitive['text'];box=font.getbbox(text);tile=Image.new('RGBA',(box[2]-box[0]+8,box[3]-box[1]+8))
            ImageDraw.Draw(tile).text((4-box[0],4-box[1]),text,font=font,fill=colour)
            tile=tile.rotate(primitive['angle'],expand=True,resample=Image.Resampling.BICUBIC)
            x,y=point(primitive['at']);im.alpha_composite(tile,(round(x-tile.width/2),round(y-tile.height/2)))
            continue
        if typ=='fp_circle':
            c=np.array(primitive['center']);r=np.linalg.norm(np.array(primitive['end'])-c)
            t=np.linspace(0,2*np.pi,80);pts=c+r*np.column_stack([np.cos(t),np.sin(t)])
        elif typ=='fp_rect':
            a,b=primitive['start'],primitive['end'];pts=[a,[b[0],a[1]],b,[a[0],b[1]],a]
        elif typ=='fp_arc':
            a,b,c=[np.array(primitive[k]) for k in ['start','mid','end']]
            centre=np.linalg.solve(2*np.array([b-a,c-a]),np.array([b@b-a@a,c@c-a@a]))
            angles=[np.arctan2(*(v-centre)[::-1]) for v in [a,b,c]]
            end=(angles[2]-angles[0])%(2*np.pi)
            if (angles[1]-angles[0])%(2*np.pi)>end:end-=2*np.pi
            t=np.linspace(angles[0],angles[0]+end,40);pts=centre+np.linalg.norm(a-centre)*np.column_stack([np.cos(t),np.sin(t)])
        elif typ=='fp_poly':pts=primitive['pts']+[primitive['pts'][0]]
        else:pts=[primitive['start'],primitive['end']]
        draw.line([point(p) for p in pts],fill=colour,width=width,joint='curve')
    im.save(GENERATED/'pcb-silkscreen.png')
    return np.asarray(im,dtype=np.float32)

SILK_TEXTURE=silkscreen_texture()

def scene(exploded=False,empty=False,config=None,length=6):
    cfg=config or CFG;data=[]
    refdir=BUILD/f'previews/meshes/m3x{length}'
    key_meshes,faces=key_meshes_and_faces(refdir)
    base=cfg['case']['base']
    data.append(item('base',load(BUILD/f'exports/base-m3x{length}.stl'),base['rgb'],base.get('opacity',1),**finish(base)))
    if not empty:
        hardware=[('nuts',[184,190,198])]
        for name,rgb in [('washers',base['rgb']),('pcb',[29,126,91]),('switches',[55,60,66]),('screen_board',[36,91,145]),('screen_glass',[16,22,28]),('screen_face',[108,184,208]),('screen_contacts',[209,174,99]),('screen_components',[52,55,59]),('screen_headers',[32,37,42]),('usb',[176,188,196]),('top_screws',[184,190,198]),*hardware]:
            shift=-14 if exploded and name=='nuts' else 28 if exploded and name=='top_screws' else 21 if exploded and name=='washers' else 14 if exploded and name not in ['top_screws','nuts'] else 0
            mesh=load(refdir/(name+'.stl'))
            if name=='top_screws':
                # Darken the recessed socket floor so the Allen drive reads from above.
                depth=json.loads(re.search(r'screw_drive = (\[[^\]]+\])',log).group(1))[1]
                socket_floor=np.all(np.isclose(mesh[:,:,2],mesh[:,:,2].max()-depth),axis=1)
                data.append(item('socket-interior',mesh[socket_floor],[60,69,79],shift=shift))
                mesh=mesh[~socket_floor]
            data.append(item(name,mesh,rgb,shift=shift))
        z=float(load(refdir/'pcb.stl')[:,:,2].max())+.012
        points=np.array([[0,60,z],[70,60,z],[70,0,z],[0,0,z]])
        ids=np.array([[0,1,2],[0,2,3]]);uv=np.array([[0,0],[1,0],[1,1],[0,1]])
        data.append(item('pcb-silkscreen',points[ids],[255,255,255],shift=14 if exploded else 0,
                         texture=SILK_TEXTURE,uv=uv[ids]))
        for i,(mesh,face,key) in enumerate(zip(key_meshes,faces,cfg['keycaps'])):
            shift=14 if exploded else 0
            data.append(item(f'keycap-{i+1}',mesh,key['rgb'],key.get('opacity',1),shift=shift))
            if key.get('image'):
                # Top of the raster points towards +Y (USB), on the centred flat cap face.
                cx,cy=face['centre'];r=face['width_mm']/2;z=face['z']+.01
                p=np.array([[cx-r,cy+r,z],[cx+r,cy+r,z],[cx+r,cy-r,z],[cx-r,cy-r,z]])
                uv=np.array([[0,0],[1,0],[1,1],[0,1]])
                ids=np.array([[0,1,2],[0,2,3]])
                texture=np.asarray(artwork_canvas(key,face['width_mm'],cfg),dtype=np.float32)
                data.append(item('artwork',p[ids],[255,255,255],shift=shift,texture=texture,uv=uv[ids]))
    return data

def render(data,name,title='',subtitle='',view=(105,-145,125),focus=None):
    eye=np.array(view,dtype=float);forward=-eye/np.linalg.norm(eye)
    right=np.cross(forward,[0,0,1])
    if np.linalg.norm(right)<1e-8:right=np.array([1.,0.,0.])
    right/=np.linalg.norm(right);up=np.cross(right,forward)
    basis=np.array([right,up,-forward]).T
    points=np.concatenate([m['mesh'].reshape(-1,3) for m in data])
    if focus is not None:
        lo,hi=focus;points=np.array([[x,y,z] for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]])
    center=(points.min(0)+points.max(0))/2
    projected=(points-center)@basis;span=np.ptp(projected[:,:2],axis=0)
    scale=min((W-100)/span[0],(H-100)/span[1]);origin=np.array([W/2,H/2])
    canvas=np.zeros((H,W,3),dtype=np.float32)+bg
    opaque_depth=np.full((H,W),-1e10,dtype=np.float32)
    light=np.array([-.3,-.4,1.]);light/=np.linalg.norm(light)

    def raster(obj,depth,colour,alpha=None,occluder=None):
        mesh=obj['mesh'];q=(mesh-center)@basis;ps=q[:,:,:2]*[scale,-scale]+origin
        norms=np.cross(mesh[:,1]-mesh[:,0],mesh[:,2]-mesh[:,0]);lengths=np.linalg.norm(norms,axis=1)
        norms/=np.maximum(lengths[:,None],1e-10)
        shades=np.clip(.47+.5*np.maximum(0,norms@light)+.08*np.maximum(0,norms@(-light)),0,1.1)
        texture=obj['texture']
        for index,(p,z,shade) in enumerate(zip(ps,q[:,:,2],shades)):
            x0=max(0,int(np.floor(p[:,0].min())));x1=min(W-1,int(np.ceil(p[:,0].max())))
            y0=max(0,int(np.floor(p[:,1].min())));y1=min(H-1,int(np.ceil(p[:,1].max())))
            if x0>x1 or y0>y1:continue
            den=(p[1,1]-p[2,1])*(p[0,0]-p[2,0])+(p[2,0]-p[1,0])*(p[0,1]-p[2,1])
            if abs(den)<1e-9:continue
            x,y=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
            a=((p[1,1]-p[2,1])*(x-p[2,0])+(p[2,0]-p[1,0])*(y-p[2,1]))/den
            b=((p[2,1]-p[0,1])*(x-p[2,0])+(p[0,0]-p[2,0])*(y-p[2,1]))/den;c=1-a-b
            zz=a*z[0]+b*z[1]+c*z[2];dest=depth[y0:y1+1,x0:x1+1]
            mask=(a>=-1e-7)&(b>=-1e-7)&(c>=-1e-7)&(zz>dest)
            if occluder is not None:mask &= zz>occluder[y0:y1+1,x0:x1+1]
            if texture is not None:
                uv=obj['uv'][index]
                u=a*uv[0,0]+b*uv[1,0]+c*uv[2,0];v=a*uv[0,1]+b*uv[1,1]+c*uv[2,1]
                tx=np.clip(np.rint(u*(texture.shape[1]-1)).astype(int),0,texture.shape[1]-1)
                ty=np.clip(np.rint(v*(texture.shape[0]-1)).astype(int),0,texture.shape[0]-1)
                sample=texture[ty,tx];opacity=sample[:,:,3]/255*obj['opacity'];mask &= opacity>0
                colours=sample[:,:,:3] # Artwork retains its sRGB colours; alpha reveals cap body.
            else:
                colours=obj['rgb']*shade;opacity=obj['opacity']
                # Small horizontal grooves on near-vertical FDM surfaces, in world mm.
                if obj['layer_height_mm']>0 and obj['layer_line_strength']>0:
                    world_z=a*mesh[index,0,2]+b*mesh[index,1,2]+c*mesh[index,2,2]
                    phase=np.mod(world_z/obj['layer_height_mm'],1)
                    groove=np.exp(-((phase-.12)/.11)**2)
                    factor=1-obj['layer_line_strength']*groove*(1-abs(norms[index,2]))
                    colours=colours[None,None,:]*factor[:,:,None]
            dest[mask]=zz[mask]
            target=colour[y0:y1+1,x0:x1+1]
            target[mask]=colours[mask] if isinstance(colours,np.ndarray) and colours.ndim==3 else colours
            if alpha is not None:
                target_alpha=alpha[y0:y1+1,x0:x1+1]
                target_alpha[mask]=opacity[mask] if texture is not None else opacity

    transparent={}
    for obj in data:
        if obj['opacity']<=0:continue
        if obj['opacity']>=1 and obj['texture'] is None:raster(obj,opaque_depth,canvas)
        else:transparent.setdefault(obj['name'],[]).append(obj)
    layers=[]
    # All six nonoverlapping top-face decals share one layer; closed translucent parts
    # retain their nearest visible surface. Layers are sorted PER PIXEL before blending.
    for objects in transparent.values():
        depth=np.full((H,W),-1e10,dtype=np.float32);colour=np.zeros((H,W,3),dtype=np.float32);alpha=np.zeros((H,W),dtype=np.float32)
        for obj in objects:raster(obj,depth,colour,alpha,opaque_depth)
        layers.append((depth,colour,alpha,objects[0]['frosted_blur_px']))
    if layers:
        depths=np.stack([v[0] for v in layers]);order=np.argsort(depths,axis=0)
        rgba=np.stack([np.concatenate([v[1],v[2][:,:,None]],axis=2) for v in layers])
        for rank in range(len(layers)):
            surface=np.take_along_axis(rgba,order[rank][None,:,:,None],axis=0)[0]
            a=surface[:,:,3:4]
            transmitted=canvas
            blur_values=np.array([v[3] for v in layers])[order[rank]]
            for radius in sorted(set(v[3] for v in layers if v[3]>0)):
                mask=(blur_values==radius)&(surface[:,:,3]>0)
                if np.any(mask):
                    if transmitted is canvas:transmitted=canvas.copy()
                    blurred=np.asarray(Image.fromarray(np.clip(canvas,0,255).astype('uint8')).filter(ImageFilter.GaussianBlur(radius)),dtype=np.float32)
                    transmitted[mask]=blurred[mask]
            canvas=surface[:,:,:3]*a+transmitted*(1-a)
    Image.fromarray(np.clip(canvas,0,255).astype('uint8')).save(BUILD/'previews'/name)
    print('Rendered',name,flush=True)

def render_exploded_nuts(length=6):
    data=scene(exploded=True,length=length)
    for obj in data:
        if obj['name']=='nuts':obj['mesh'][:,:,2]-=20
    render(data,f'exploded-m3x{length}.png',view=(80,-110,75))

def render_screen_shelf():
    # Hide keys and fasteners to expose the small gap below the OLED in this detail.
    visible={'base','pcb','pcb-silkscreen','screen_board','screen_glass','screen_face','screen_contacts','screen_components','screen_headers'}
    render([obj for obj in scene() if obj['name'] in visible],'screen-shelf.png',
           view=(100,-40,25),focus=([20,55,4],[62,62,12]))

if __name__=='__main__':
    import argparse
    import subprocess
    import sys
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets-only',action='store_true',help='Refresh mesh reports and artwork without rendering assemblies')
    args=parser.parse_args()
    CFG=load_config();sync_scad(CFG)
    results=[validate(BUILD/'exports'/n) for n in ['base-m3x6.stl','accessories/washer-0.6mm.stl','accessories/nut-fit-test-m3.stl']]
    (BUILD/'exports/mesh-checks.json').write_text(json.dumps(results,indent=2)+'\n')
    manifest=export_print_pack(CFG,FACES)
    print(f'Print pack: six key assignments, {len(manifest["generated_files"])//2} unique artwork designs.',flush=True)
    if not args.assets_only:
        for script in ['preview_top_frame.py','frame_section.py']:
            subprocess.run([sys.executable,str(Path(__file__).with_name(script))],check=True)
