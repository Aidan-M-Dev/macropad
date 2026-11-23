"""Material study of the open-top case in frosted natural PETG."""
import copy,json
from appearance import load_config
from paths import GENERATED
import preview
variant=copy.deepcopy(load_config())
variant['case']['base']={'rgb':[215,225,228],'opacity':0.58,'frosted_blur_px':4.0,
                         'layer_height_mm':preview.print_dims[1],'layer_line_strength':0.09}
settings=GENERATED/'appearance-petg-base-translucent.json'
settings.write_text(json.dumps(variant,indent=2)+'\n')
preview.render(preview.scene(config=load_config(settings)),'petg-base-translucent.png')
