/* IC Hack macropad enclosure, mm.
   Origin: PCB lower-left, USB edge at +Y; assembled base underside Z=0.
   Four M3 through-screws, insulating washers and underside hex nuts.
   See README.md for dimensions, assembly and print orientation. */
/* [Hidden] */
include <../build/generated/pcb_geometry.scad>
include <../build/generated/appearance.scad>
include <../accessories/parts.scad>

/* [View and export] */
part = "assembly"; // [top_frame,top_frame_assembled,assembly,exploded,section,print,base,washer,washer_set,nut_fit_test,screen_shelf,washers,pcb,nuts,keys,switches,keycaps,screen,screen_board,screen_glass,screen_pixels,screen_face,screen_contacts,screen_components,screen_headers,usb,top_screws,check_washers,check_hardware_electronics,check_pcb,check_screen,check_screen_insertion,check_keys,check_usb,check_underside,check_fasteners]
show_electronics = true;
show_fasteners = true;
with_top_frame = true;
explosion = 14;
quality = 48;

/* [PCB fit] */
pcb_clearance = 0.35;
board_thickness = 1.6;
// Required free space from inside floor to PCB underside, including solder/components.
underside_clearance = 3.5;

/* [Print dimensions] */
nozzle_diameter = 0.4;
layer_height = 0.2;
extrusion_width_factor = 1.0;
wall_count = 2;
bottom_layers = 2;
rib_enabled = false;
rib_wall_count = 2;
rib_height_layers = 8;

/* [Shell and local reinforcement] */
corner_radius = 2.4;
edge_round_layers = 1;
bottom_edge_radius = 0.6;
bottom_corner_radius = 4.0;
bottom_corner_blend_height = 2.4;
rim_above_pcb_top = 2.2;
boss_wall_count = 2;
collar_wall_count = 2;
bearing_min_mm = 1.2;
bearing_min_layers = 3;
washer_thickness = 0.6;
washer_d = 5.0;

/* [M3 hex-socket screws] */
// Under-head length. Case height follows this length; the tip stays recessed.
screw_length = 6; // Original compact-base datum; the reinforced frame uses M3x12.
screw_clearance_d = 3.4;
screw_nominal_d = 3.0;
head_d = 5.5;
head_h = 3.0;
socket_af = 2.5;
socket_depth = 1.3;
minimum_thread_engagement = 2.0;

/* [Underside M3 nuts] */
nut_af = 5.5;
nut_height = 2.4;
// TOTAL across-flats allowance, not per side. Enlarged after the 5.60 mm case fit was tight.
nut_fit_allowance = 0.20;
nut_inset = 0.4;
nut_leadin = 0.25;
// Seven 0.2 mm layers; permits the compact M3x6 stack while retaining a sloped roof.
nut_roof_height = 1.4;
nut_taper_height = 1.4;
nut_seat_width = 0.25;

/* [Keycaps - outlines from Dwgs.User] */
keycap_preview_width = 18.3;
keycap_preview_bottom = 6.5;
keycap_preview_height = 8.0;
key_travel = 4.0;
switch_lower_width = 14.0;
switch_lower_height = 1.5;
switch_upper_width = 13.6;
switch_upper_top_width = 11.6;
switch_body_height = 5.2;
switch_stem_width = 4.0;
switch_stem_bar = 1.2;
switch_stem_top = 6.8;

/* [OLED reference] */
// Assumed header housing height, from the prototype.
screen_mount_gap = 2.5;
// Target top above the main PCB; round DOWN to printable layers for slide clearance.
screen_shelf_height = 2.25;
// Relief around the OLED header housings, including insertion room.
screen_shelf_clearance = 0.5;
// Minimum overlap; a shallower underside slope can extend the shelf further.
screen_shelf_overlap = 1.2;
// Underside angle measured above the print bed.
screen_shelf_slope_angle = 30;
screen_shelf_leadin = 0.25;
screen_shelf_board_clearance = 0.25;
screen_header_width = 2.5;
screen_board_thickness = 1.0;
screen_glass_height = 1.6;
screen_panel_width = 30.0;
screen_panel_depth = 11.5;
screen_panel_left = 5.0;
screen_panel_bottom = 0.25;
screen_face_rim = 0.6;
screen_preview_active_only = false;
screen_contact_d = 1.8;
screen_contact_hole_d = 1.0;
screen_pin_width = 0.6;
screen_component_height = 0.5;
screen_offset_x = 0;
screen_offset_y = 0;

/* [Underside USB-C connector] */
// Measured just under 10 mm wide, extending 3.5 mm below the PCB underside.
usb_body_width = 9.8;
usb_body_height = 3.5;
usb_opening_width = 10.4;
usb_bottom_clearance = 0.3;
usb_corner_radius = 0.5;
// Initial roof thickness before filling the top 3 mm of the original port.
usb_bridge_layers = 4;
usb_top_reduction = 3.0;
usb_x_offset = 0;

/* [Hidden] */
$fn = quality;
eps = 0.02;
function layer_up(v) = ceil(v/layer_height-0.000001)*layer_height;
line_width = nozzle_diameter*extrusion_width_factor;
wall = wall_count*line_width;
base_skin = bottom_layers*layer_height;
rib_width = rib_wall_count*line_width;
rib_height = rib_height_layers*layer_height;
rib_top = base_skin + (rib_enabled ? rib_height : 0);
minimum_bearing = layer_up(max(bearing_min_mm,bearing_min_layers*layer_height));
top_screw_land = layer_up(washer_thickness);
washer_outer_d = max(washer_d,screw_clearance_d+4*line_width);
nut_pocket_af = nut_af+nut_fit_allowance;
nut_pocket_top = layer_up(nut_inset+nut_height);
nut_taper_h = layer_up(nut_taper_height);
nut_taper_start_af = nut_pocket_af-2*nut_seat_width;
nut_boss_height = nut_pocket_top+layer_up(nut_roof_height);
nut_tube_d = screw_clearance_d+2*collar_wall_count*line_width;
nut_entry_af = nut_pocket_af+2*nut_leadin;
base_boss_d = nut_entry_af/cos(30)+2*boss_wall_count*line_width;
outer_corner_radius = max(corner_radius,wall+line_width/2);
edge_round = min(edge_round_layers*layer_height,0.45*min(wall,base_skin));
bottom_round = min(bottom_edge_radius,0.9*wall);
lower_corner_radius = max(outer_corner_radius,bottom_corner_radius);
w = pcb_pcb_size[0]; d = pcb_pcb_size[1];
pad = pcb_clearance + wall;
outer_w = w + 2*pad; outer_d = d + 2*pad;
// Align screw tip with nut bottom for full engagement, both inset from the base.
// Round UP so printing at other layer heights never lowers the PCB clearance.
pcb_bottom = layer_up(screw_length+nut_pocket_top-nut_height-board_thickness-top_screw_land);
pcb_top = pcb_bottom+board_thickness;
case_top = layer_up(pcb_top+rim_above_pcb_top);
top_screw_length = screw_length;
top_screw_tip = pcb_top+top_screw_land-top_screw_length;
top_engagement = min(nut_height,nut_pocket_top-top_screw_tip);
usb_opening_bottom = pcb_bottom-usb_body_height-usb_bottom_clearance;
usb_original_opening_top = case_top-usb_bridge_layers*layer_height;
usb_opening_top = usb_original_opening_top-usb_top_reduction;
usb_bridge_height = case_top-usb_opening_top;
usb_opening_height = usb_opening_top-usb_opening_bottom;
screen_body = [pcb_oled_body_bounds[0]+screen_offset_x,pcb_oled_body_bounds[1]+screen_offset_y,pcb_oled_body_bounds[2]+screen_offset_x,pcb_oled_body_bounds[3]+screen_offset_y];
screen_view = [pcb_oled_view_bounds[0]+screen_offset_x,pcb_oled_view_bounds[1]+screen_offset_y,pcb_oled_view_bounds[2]+screen_offset_x,pcb_oled_view_bounds[3]+screen_offset_y];
screen_shelf_top = floor((pcb_top+screen_shelf_height)/layer_height+0.000001)*layer_height;
screen_shelf_x = screen_body[0];
screen_shelf_end = screen_body[2];
screen_shelf_width = screen_shelf_end-screen_shelf_x;
screen_shelf_rise = screen_shelf_top-screen_shelf_leadin-pcb_top-screen_shelf_board_clearance;
screen_shelf_run = screen_shelf_slope_angle>0 && screen_shelf_slope_angle<90 ?
    screen_shelf_rise/tan(screen_shelf_slope_angle) : 0;
screen_shelf_front = min(screen_body[3]-screen_shelf_overlap,d+pcb_clearance-screen_shelf_run);
screen_shelf_actual_overlap = screen_body[3]-screen_shelf_front;
screen_shelf_back = d+pcb_clearance+wall/2;
case_height = max(case_top,screen_shelf_top);
screen_top = pcb_top+screen_mount_gap+screen_board_thickness+screen_glass_height;
screen_panel_bounds = [screen_body[0]+screen_panel_left,screen_body[1]+screen_panel_bottom,
    screen_body[0]+screen_panel_left+screen_panel_width,screen_body[1]+screen_panel_bottom+screen_panel_depth];
screen_face_bounds = screen_preview_active_only ? screen_view :
    [screen_panel_bounds[0]+screen_face_rim,screen_panel_bounds[1]+screen_face_rim,
     screen_panel_bounds[2]-screen_face_rim,screen_panel_bounds[3]-screen_face_rim];

include <top_frame_modules.scad>

assert(screen_face_rim>0 && 2*screen_face_rim<min(screen_panel_width,screen_panel_depth),"Invalid screen face rim");
assert(socket_af>0 && socket_af/cos(30)<head_d && socket_depth>0 && socket_depth<head_h,"Invalid hex socket dimensions");
assert(nozzle_diameter>0 && layer_height>0 && extrusion_width_factor>0,"Print dimensions must be positive");
assert(wall_count>=2 && bottom_layers>=2,"Use at least two walls/skin layers");
assert(pcb_clearance>0 && wall>0 && base_skin>0,"Invalid shell thickness or PCB fit clearance");
assert(!rib_enabled || (rib_wall_count>=2 && rib_height_layers>=3),"Ribs need at least two lines and three layers");
assert(pcb_bottom-rib_top>=underside_clearance-0.000001,"Insufficient underside clearance");
assert(screw_length>0 && board_thickness>0);
assert(edge_round>0 && edge_round<min(wall,base_skin)/2,"Edge round too large");
assert(corner_radius>edge_round && corner_radius<min(outer_w,outer_d)/2);
assert(bottom_round>0 && bottom_corner_blend_height>=bottom_round && bottom_corner_blend_height<pcb_bottom,"Invalid lower edge rounding");
assert(lower_corner_radius<min(outer_w,outer_d)/2 && lower_corner_radius>bottom_round,"Invalid lower corner radius");
assert(rim_above_pcb_top>=layer_height && case_top>=pcb_top+layer_height-0.000001,"Rim must protect PCB edge by at least one layer");
assert(case_top<pcb_top+keycap_preview_bottom-key_travel,"Rim reaches pressed keycap height");
assert(washer_thickness>=0.6 && top_screw_land>=3*layer_height-0.000001,"Insufficient washer thickness");
assert(head_d>screw_clearance_d && washer_outer_d>=screw_clearance_d+4*line_width-0.000001,"Insufficient radial bearing material");
assert(nut_af>screw_clearance_d && nut_height>=minimum_thread_engagement && nut_pocket_af>screw_clearance_d,"Invalid nut dimensions");
assert(nut_inset>=0 && nut_leadin>0 && nut_leadin<nut_height && nut_entry_af>=nut_af,"Invalid nut entry lead-in");
assert(nut_boss_height-nut_pocket_top>=minimum_bearing-0.000001 && nut_boss_height<=pcb_bottom+0.000001,"Insufficient bearing above nut pocket");
assert(nut_taper_height>=0 && nut_taper_h<=nut_boss_height-nut_pocket_top+0.000001,"Nut roof taper must fit inside widened boss");
assert(nut_taper_h==0 || (nut_seat_width>0 && nut_taper_start_af>screw_clearance_d),"Invalid nut bearing ledge");
assert(nut_taper_h==0 || nut_taper_h>=(nut_taper_start_af/cos(30)-screw_clearance_d)/2,"Nut roof taper too steep; use at most 45 degrees from vertical");
assert(nut_tube_d<base_boss_d && collar_wall_count>=2,"Invalid printed support wall");
assert(top_screw_tip>=-0.000001 && top_screw_tip<=nut_pocket_top-nut_height+0.000001,"Screw must fully engage nut without protruding below base");
assert(usb_opening_width>=usb_body_width+0.4 && usb_bottom_clearance>=0.2,"Insufficient USB opening clearance");
assert(usb_opening_bottom>=base_skin-0.000001,"USB opening cuts through bottom skin");
assert(usb_bridge_layers>=2,"USB bridge needs at least two layers");
assert(usb_top_reduction>=0 && abs(usb_top_reduction/layer_height-round(usb_top_reduction/layer_height))<0.001,
       "USB top reduction must be nonnegative and use whole print layers");
// The requested 3 mm crop puts the roof at the nominal connector top.
assert(usb_opening_top>=pcb_bottom-0.000001,"Insufficient clearance above USB connector");
assert(usb_opening_height>2*usb_corner_radius && usb_opening_width>2*usb_corner_radius);

assert(screen_shelf_top<=pcb_top+screen_mount_gap-0.2+0.000001,"Shelf needs at least 0.2 mm clearance below screen");
assert(abs(screen_shelf_top-case_top)<0.000001,"Rim must match screen shelf height");
assert(screen_shelf_overlap>screen_shelf_leadin && screen_shelf_width>=3*line_width,"Insufficient screen shelf bearing area");
assert(screen_shelf_clearance>=0.5,"Shelf needs insertion clearance around components");
assert(screen_shelf_slope_angle>0 && screen_shelf_slope_angle<90,"Invalid screen shelf slope angle");
assert(screen_shelf_board_clearance>=0.2 && screen_shelf_top-screen_shelf_leadin>pcb_top+screen_shelf_board_clearance,"Shelf must leave main PCB clear");
assert(screen_shelf_front>screen_body[1] && screen_body[3]<d+pcb_clearance,"Shelf must overlap rear edge of screen");
assert((d+pcb_clearance-screen_shelf_front)*layer_height/(screen_shelf_top-screen_shelf_leadin-pcb_top-screen_shelf_board_clearance)<=line_width,"Shelf underside overhang exceeds one line per layer");

echo(screw_drive=[socket_af,socket_depth]);
echo(fastener_radial=[screw_clearance_d,washer_outer_d,screw_nominal_d,head_d,head_h]);
echo(print_dimensions=[line_width,layer_height,wall,base_skin,rib_enabled ? rib_width : 0,rib_enabled ? rib_height : 0]);
echo(top_screw_length=top_screw_length,rim_above_pcb_top=case_top-pcb_top);
echo(nut_stack=[nut_af,nut_height,nut_pocket_af,nut_pocket_top,top_screw_tip,top_engagement]);
echo(nut_support=[nut_boss_height,nut_tube_d,pcb_bottom-nut_boss_height]);
echo(nut_roof_taper=[nut_taper_h,nut_seat_width,nut_taper_start_af]);
echo(lower_edge=[bottom_round,lower_corner_radius,bottom_corner_blend_height],ribs_enabled=rib_enabled);
echo(fastener_walls=[boss_wall_count*line_width,collar_wall_count*line_width,(washer_outer_d-screw_clearance_d)/2],nut_entry=[nut_entry_af,nut_leadin]);
echo(case_size=[outer_w,outer_d,case_height],pcb_bottom=pcb_bottom,pcb_top=pcb_top);
echo(washer=[washer_outer_d,screw_clearance_d,top_screw_land]);
echo(underside_space=pcb_bottom-rib_top,required_underside_space=underside_clearance);
echo(usb_opening=[usb_opening_width,usb_opening_height,usb_opening_bottom],usb_body=[usb_body_width,usb_body_height]);
echo(usb_bridge=[usb_bridge_height,usb_opening_top,case_top]);
echo(usb_top_crop=[usb_top_reduction,usb_opening_top-pcb_bottom]);

echo(screen_shelf=[screen_shelf_top-pcb_top,screen_mount_gap,pcb_top+screen_mount_gap-screen_shelf_top,screen_shelf_width,screen_shelf_actual_overlap]);
echo(screen_shelf_bounds=[screen_shelf_x,screen_shelf_front,screen_shelf_end,screen_shelf_back,screen_shelf_top]);
echo(screen_shelf_slope=atan(screen_shelf_rise/(d+pcb_clearance-screen_shelf_front)),screen_shelf_clearance=screen_shelf_clearance);

module rr2(x,y,r) {
    assert(x>2*r && y>2*r && r>0,"Invalid rounded rectangle");
    hull() for(a=[r,x-r],b=[r,y-r]) translate([a,b]) circle(r=r);
}
module outer_profile(inset=0,radius=outer_corner_radius) {
    translate([-pad+inset,-pad+inset]) rr2(outer_w-2*inset,outer_d-2*inset,radius-inset);
}
function lower_inset(z) = z>=bottom_round ? 0 : bottom_round-sqrt(max(0,2*bottom_round*z-z*z));
function lower_corner(z) = outer_corner_radius+(lower_corner_radius-outer_corner_radius)*
    (z>=bottom_corner_blend_height ? 0 : (1+cos(180*z/bottom_corner_blend_height))/2);
// Blend the broader bottom corners into the original outline below the PCB.
module soft_outer(z,h,lower=true,upper=true) {
    n=4; r=edge_round; lower_h=lower ? bottom_corner_blend_height : 0;
    translate([0,0,z]) {
        translate([0,0,lower_h]) linear_extrude(height=h-lower_h-(upper?r:0)) outer_profile();
        // Concentrate sections near Z=0 to resolve the small underside round-over.
        if(lower) for(i=[0:11]) hull() for(j=[i,i+1]) {
            zz=lower_h*pow(j/12,2);
            translate([0,0,zz]) linear_extrude(height=0.001) outer_profile(lower_inset(zz),lower_corner(zz));
        }
        if(upper) for(i=[0:n-1]) hull() for(j=[i,i+1]) {
            a=90*j/n;
            translate([0,0,h-r+r*sin(a)-0.001]) linear_extrude(height=0.001) outer_profile(r*(1-cos(a)));
        }
    }
}
module cavity(z,h) {
    // Follow the lower outside corners, retaining the two-line corner walls.
    if(z<bottom_corner_blend_height) for(i=[0:11]) {
        za=max(z,bottom_corner_blend_height*pow(i/12,2));
        zb=bottom_corner_blend_height*pow((i+1)/12,2);
        if(zb>za) hull() for(zz=[za,zb])
            translate([-pcb_clearance,-pcb_clearance,zz]) linear_extrude(height=0.001)
                rr2(w+2*pcb_clearance,d+2*pcb_clearance,lower_corner(zz)-wall);
    }
    translate([-pcb_clearance,-pcb_clearance,max(z,bottom_corner_blend_height)])
        linear_extrude(height=h) rr2(w+2*pcb_clearance,d+2*pcb_clearance,outer_corner_radius-wall);
}
module bounds_prism(b,clear,z,h,r=0.4) {
    translate([b[0]-clear,b[1]-clear,z])
        linear_extrude(height=h) rr2(b[2]-b[0]+2*clear,b[3]-b[1]+2*clear,r);
}
module cable_cut() {
    // Crop the old rounded port from above: retain its bottom and lower corners,
    // but make the lowered ceiling flat so it clears the full connector width.
    translate([pcb_usb_centre[0]+usb_x_offset-usb_opening_width/2,d+pad+eps,usb_opening_bottom])
        rotate([90,0,0]) linear_extrude(height=2*pad+5)
            intersection() {
                rr2(usb_opening_width,usb_original_opening_top-usb_opening_bottom,usb_corner_radius);
                square([usb_opening_width,usb_opening_height]);
            }
}
module floor_network() {
    if(rib_enabled) translate([0,0,base_skin-eps])
        linear_extrude(height=rib_height+eps)
            // Rectangle through all four mounting points, plus both diagonals.
            for(pair=[[0,1],[1,3],[3,2],[2,0],[0,3],[1,2]]) hull()
                for(i=pair) translate(pcb_mount_holes[i]) circle(d=rib_width);
}
module nut_outer_profile(af) {
    offset(r=boss_wall_count*line_width) nut_profile(af);
}
module nut_support(pocket_af=nut_pocket_af,support_top=pcb_bottom) {
    entry_af=pocket_af+2*nut_leadin;
    linear_extrude(height=nut_pocket_top) nut_outer_profile(pocket_af);
    hull() {
        linear_extrude(height=eps) nut_outer_profile(entry_af);
        translate([0,0,nut_leadin]) linear_extrude(height=eps) nut_outer_profile(pocket_af);
    }
    hull() {
        translate([0,0,nut_pocket_top-eps]) linear_extrude(height=eps) nut_outer_profile(pocket_af);
        translate([0,0,nut_boss_height-eps]) cylinder(d=nut_tube_d,h=eps);
    }
    if(support_top>nut_boss_height+eps)
        translate([0,0,nut_boss_height-eps]) cylinder(d=nut_tube_d,h=support_top-nut_boss_height+eps);
}
// Shared by the enclosure and nut-fit coupon, including the same lead-in and roof.
module nut_pocket(pocket_af=nut_pocket_af,bore_height=pcb_bottom) {
    entry_af=pocket_af+2*nut_leadin;
    translate([0,0,-eps]) cylinder(d=screw_clearance_d,h=bore_height+2*eps);
    translate([0,0,-eps]) linear_extrude(height=nut_pocket_top+eps) nut_profile(pocket_af);
    translate([0,0,-eps]) linear_extrude(height=nut_leadin+eps,scale=pocket_af/entry_af)
        nut_profile(entry_af);
    if(nut_taper_h>0) hull() {
        translate([0,0,nut_pocket_top-eps]) linear_extrude(height=eps)
            nut_profile(pocket_af-2*nut_seat_width);
        translate([0,0,nut_pocket_top+nut_taper_h-eps]) cylinder(d=screw_clearance_d,h=eps);
    }
}
module screen_shelf() {
    // Support the full OLED width with a 30-degree underside and header relief.
    difference() {
        translate([screen_shelf_x,0,0]) rotate([90,0,90])
            linear_extrude(height=screen_shelf_width) polygon([
                [screen_shelf_front,screen_shelf_top-screen_shelf_leadin],
                [screen_shelf_front+screen_shelf_leadin,screen_shelf_top],
                [screen_shelf_back,screen_shelf_top],
                [screen_shelf_back,pcb_top+screen_shelf_board_clearance],
                [d+pcb_clearance,pcb_top+screen_shelf_board_clearance]
            ]);
        // The last header housing lies beneath the shelf; allow it to tilt in.
        for(p=pcb_oled_pins)
            translate([p[0]+screen_offset_x-screen_header_width/2-screen_shelf_clearance,
                       p[1]+screen_offset_y-1.27-screen_shelf_clearance,pcb_top-eps])
                cube([screen_header_width+2*screen_shelf_clearance,2.54+2*screen_shelf_clearance,
                      case_top-pcb_top+2*eps]);
    }
}
module base() {
    difference() {
        union() {
            difference() {
                soft_outer(0,case_top,true,true);
                cavity(base_skin,case_top+eps);
            }
            floor_network();
            screen_shelf();
            for(p=pcb_mount_holes) translate([p[0],p[1],0]) nut_support();
        }
        for(p=pcb_mount_holes) translate([p[0],p[1],0]) nut_pocket();
        cable_cut();
    }
}
// Fit references, not component CAD. XY follows PCB; adjustable Z assumptions above.
module pcb_proxy() {
    difference() {
        translate([0,0,pcb_bottom]) linear_extrude(height=board_thickness) rr2(w,d,1);
        for(p=pcb_mount_holes) translate([p[0],p[1],pcb_bottom-eps]) cylinder(d=3.2,h=board_thickness+2*eps);
        translate([pcb_usb_centre[0]-4.57,d-4.51,pcb_bottom-eps]) cube([9.14,5,board_thickness+2*eps]);
    }
}
module nut_profile(af) {rotate(30) circle(d=af/cos(30),$fn=6);}
module nuts() {
    for(p=pcb_mount_holes) translate([p[0],p[1],nut_pocket_top-nut_height]) difference() {
        linear_extrude(height=nut_height) nut_profile(nut_af);
        translate([0,0,-eps]) cylinder(d=2.5,h=nut_height+2*eps);
    }
}
// Scale about the centre of the profile; corner-anchored scaling offsets the top.
module centred_rr2(width,r) {
    translate([-width/2,-width/2]) rr2(width,width,r);
}
module switches() {
    for(p=pcb_key_centres) translate([p[0],p[1],pcb_top]) {
        translate([0,0,switch_lower_height/2])
            cube([switch_lower_width,switch_lower_width,switch_lower_height],center=true);
        translate([0,0,switch_lower_height])
            linear_extrude(height=switch_body_height-switch_lower_height,
                           scale=switch_upper_top_width/switch_upper_width)
                centred_rr2(switch_upper_width,0.7);
        translate([0,0,switch_body_height]) linear_extrude(height=switch_stem_top-switch_body_height)
            union() {
                square([switch_stem_width,switch_stem_bar],center=true);
                square([switch_stem_bar,switch_stem_width],center=true);
            }
    }
}
function rgb01(rgb) = [for(c=rgb) c/255];
module keycaps() {
    for(i=[0:len(pcb_key_centres)-1])
        color(rgb01(appearance_keycap_rgbs[i]),appearance_keycap_opacities[i])
        translate([pcb_key_centres[i][0],pcb_key_centres[i][1],pcb_top+keycap_preview_bottom])
            linear_extrude(height=keycap_preview_height,scale=0.8)
                centred_rr2(keycap_preview_width,1);
}
module keys() {
    color("#373c42") switches();
    keycaps();
}
module screen_board() {
    difference() {
        bounds_prism(screen_body,0,pcb_top+screen_mount_gap,screen_board_thickness);
        for(p=pcb_oled_pins) translate([p[0]+screen_offset_x,p[1]+screen_offset_y,pcb_top+screen_mount_gap-eps])
            cylinder(d=screen_contact_hole_d,h=screen_board_thickness+2*eps);
    }
}
module screen_glass() {
    // Recess the active face into the black panel. There is no overlapping full blue block.
    difference() {
        translate([screen_body[0]+screen_panel_left,screen_body[1]+screen_panel_bottom,
                   pcb_top+screen_mount_gap+screen_board_thickness])
            cube([screen_panel_width,screen_panel_depth,screen_glass_height]);
        bounds_prism(screen_face_bounds,0,screen_top-0.03,0.03+eps,0.02);
    }
}
module screen_pixels() {
    // Exact 128x32 pixel-area reference, kept at its true size for measurement.
    bounds_prism(screen_view,0,screen_top-0.03,0.03,0.02);
}
module screen_face() {
    // Larger visible face for the rough visualisation, flush within a narrow black rim.
    bounds_prism(screen_face_bounds,0,screen_top-0.03,0.03,0.02);
}
module screen_contacts() {
    for(p=pcb_oled_pins) translate([p[0]+screen_offset_x,p[1]+screen_offset_y,pcb_top]) {
        translate([-screen_pin_width/2,-screen_pin_width/2,0])
            cube([screen_pin_width,screen_pin_width,screen_mount_gap+screen_board_thickness+0.35]);
        translate([0,0,screen_mount_gap+screen_board_thickness]) difference() {
            cylinder(d=screen_contact_d,h=0.04);
            translate([0,0,-eps]) cylinder(d=screen_contact_hole_d,h=0.04+2*eps);
        }
    }
}
module screen_components() {
    // Indicative component bodies in the exposed strip, not individual manufacturer CAD.
    for(dy=[1.8,4.5,7.2,9.9])
        translate([screen_body[2]-2.1,screen_body[1]+dy-0.7,
                   pcb_top+screen_mount_gap+screen_board_thickness])
            cube([1.2,1.4,screen_component_height]);
}
module screen_headers() {
    // Four insulating header housings, 2.5 mm tall, beneath the OLED PCB.
    for(p=pcb_oled_pins) translate([p[0]+screen_offset_x-screen_header_width/2,p[1]+screen_offset_y-1.27,pcb_top])
        cube([screen_header_width,2.54,screen_mount_gap]);
}
module screen() {
    color("#20252a") screen_headers();
    color("#245b91") screen_board();
    color("#10161c") screen_glass();
    color("#6cb8d0") screen_face();
    color("#d1ae63") screen_contacts();
    color("#34373b") screen_components();
}
module usb_proxy() {
    translate([pcb_usb_centre[0]+usb_x_offset-usb_body_width/2,d-4.5,pcb_bottom-usb_body_height])
        cube([usb_body_width,5,usb_body_height]);
}
module socket_head() {
    difference() {
        cylinder(d=head_d,h=head_h);
        translate([0,0,head_h-socket_depth]) rotate([0,0,30])
            cylinder(d=socket_af/cos(30),h=socket_depth+eps,$fn=6);
    }
}
module top_screws() {
    land = with_top_frame ? frame_screw_land : top_screw_land;
    length = with_top_frame ? screw_length + frame_screw_extra : top_screw_length;
    for(p=pcb_mount_holes) translate([p[0],p[1],pcb_top+land]) {
        socket_head();
        translate([0,0,-length]) cylinder(d=screw_nominal_d,h=length+eps);
    }
}
// Inset the head/shaft envelopes to ignore intentional contact at bearing faces.
module fastener_keepout() {
    for(p=pcb_mount_holes) translate([p[0],p[1],0]) {
        translate([0,0,top_screw_tip+eps]) cylinder(d=screw_nominal_d-2*eps,h=top_screw_length-2*eps);
        translate([0,0,pcb_top+top_screw_land+eps]) cylinder(d=head_d-2*eps,h=head_h-2*eps);

    }
}
module assembly(explode=0) {
    color(rgb01(appearance_case_base_rgb),appearance_case_base_opacity) base();
    if(!with_top_frame) color(rgb01(appearance_case_base_rgb)) translate([0,0,1.5*explode]) washers();
    if(with_top_frame) {
        color(rgb01(appearance_case_frame_rgb),appearance_case_frame_opacity) translate([0,0,1.7*explode]) top_frame();
    }
    if(show_electronics) {
        color(rgb01(appearance_board_rgb)) translate([0,0,explode]) pcb_proxy();
        color("#d1d7d9") translate([0,0,explode]) usb_proxy();
        color("#373c42") translate([0,0,with_top_frame ? 2.5*explode : explode]) switches();
        translate([0,0,with_top_frame ? 3.5*explode : explode]) keycaps();
        translate([0,0,explode]) screen();
    }
    if(show_fasteners) {
        color("#b1b9c2") translate([0,0,with_top_frame ? 4*explode : 2*explode]) top_screws();
        color("#b1b9c2") translate([0,0,-explode]) nuts();
    }
}
module shells() {base();}
module key_keepout() {
    // Full-height travel envelopes from the drawn 1u outlines.
    for(b=pcb_keycap_bounds) bounds_prism(b,0,pcb_top,case_top+keycap_preview_height,0.01);
}
// Full underside component envelope; mounting hardware has its own corner keepouts.
module underside_keepout() {
    difference() {
        translate([0,0,pcb_bottom-underside_clearance])
            linear_extrude(height=underside_clearance) rr2(w,d,1);
        for(p=pcb_mount_holes) translate([p[0],p[1],pcb_bottom-underside_clearance-eps])
            cylinder(d=base_boss_d+0.6,h=underside_clearance+2*eps);
    }
}
module screen_keepout() {bounds_prism(screen_body,0,pcb_top+screen_mount_gap,screen_board_thickness+screen_glass_height);}
if(part=="top_frame") color(rgb01(appearance_case_frame_rgb),appearance_case_frame_opacity) top_frame_print();
else if(part=="top_frame_assembled") color(rgb01(appearance_case_frame_rgb),appearance_case_frame_opacity) top_frame();
else if(part=="check_frame_electronics") intersection() {
    top_frame(); union() {
        // Exclude the intentional foot/PCB bearing contact at the top face.
        intersection() {
            pcb_proxy();
            translate([-pad,-pad,pcb_bottom+eps]) cube([outer_w,outer_d,board_thickness-2*eps]);
        }
        switches();screen();usb_proxy();
    }
}
else if(part=="check_frame_base") intersection() {top_frame();base();}
else if(part=="check_frame_hardware") intersection() {
    top_frame();
    // Bearing contact at the flat top face is intentional.
    for(p=pcb_mount_holes) translate([p[0],p[1],0]) {
        translate([0,0,frame_screw_tip+eps])
            cylinder(d=screw_nominal_d,h=screw_length+frame_screw_extra-2*eps);
        translate([0,0,pcb_top+frame_screw_land+eps]) cylinder(d=head_d,h=head_h-2*eps);
    }
}
else if(part=="base") color(rgb01(appearance_case_base_rgb),appearance_case_base_opacity) base();
else if(part=="washer") washer();
else if(part=="nut_fit_test") nut_fit_test();
else if(part=="screen_shelf") screen_shelf();
else if(part=="washers") washers();
else if(part=="washer_set") for(i=[0:3]) translate([(i%2)*8,floor(i/2)*8,0]) washer();
else if(part=="print") {
    base();
    if(with_top_frame) translate([outer_w+8,0,0]) top_frame_print();
    else for(i=[0:3]) translate([w+pad+8+(i%2)*9,12+floor(i/2)*9,0]) washer();
}
else if(part=="exploded") assembly(explosion);
else if(part=="section") intersection() {
    assembly(); translate([-pad-1,pcb_mount_holes[2][1],-5]) cube([outer_w+2,outer_d,case_top+40]);
}
else if(part=="pcb") pcb_proxy();
else if(part=="nuts") nuts();
else if(part=="keys") keys();
else if(part=="switches") switches();
else if(part=="keycaps") keycaps();
else if(part=="screen") screen();
else if(part=="screen_board") screen_board();
else if(part=="screen_glass") screen_glass();
else if(part=="screen_pixels") screen_pixels();
else if(part=="screen_face") screen_face();
else if(part=="screen_contacts") screen_contacts();
else if(part=="screen_components") screen_components();
else if(part=="screen_headers") screen_headers();
else if(part=="usb") usb_proxy();
else if(part=="top_screws") top_screws();
// Ignore intentional face contact at the PCB / washer clamp interface.
else if(part=="check_pcb") intersection() {
    shells();
    intersection() {
        pcb_proxy();
        translate([-1,-1,pcb_bottom+eps]) cube([w+2,d+2,board_thickness-2*eps]);
    }
}
else if(part=="check_hardware_electronics") intersection() {
    union() {washers();top_screws();}
    union() {key_keepout();screen();pcb_proxy();}
}
else if(part=="check_washers") intersection() {shells();washers();}
// Nose-first placement: rear edge under the ledge, then lower the front.
// Use positive tilt angles so intentional final PCB/support contact is excluded.
else if(part=="check_screen_insertion") intersection() {
    shells();
    union() for(angle=[2,4,6]) translate([0,d,pcb_bottom]) rotate([-angle,0,0]) translate([0,-d,-pcb_bottom])
        union() {pcb_proxy();screen();usb_proxy();}
}
else if(part=="check_screen") intersection() {shells();union() {screen_keepout();screen();}}
else if(part=="check_keys") intersection() {shells();key_keepout();}
else if(part=="check_underside") intersection() {shells();underside_keepout();}
else if(part=="check_usb") intersection() {
    shells();
    // The cropped roof meets the nominal connector top. Ignore that intentional
    // bearing face (and CSG rounding there), as at the PCB/support interfaces.
    intersection() {
        usb_proxy();
        translate([-1,-1,-1]) cube([w+2,d+2,pcb_bottom+1-eps]);
    }
}
else if(part=="check_fasteners") intersection() {shells();fastener_keepout();}
else {assert(part=="assembly","Unknown part");assembly();}
