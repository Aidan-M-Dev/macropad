// Shared accessory modules. Loaded by case/macropad_case.scad, which supplies
// the dimensions and nut-pocket geometry used by the enclosure.

module washer() {
    difference() {
        cylinder(d=washer_outer_d,h=top_screw_land);
        translate([0,0,-eps]) cylinder(d=screw_clearance_d,h=top_screw_land+2*eps);
    }
}
module washers() {
    for(p=pcb_mount_holes) translate([p[0],p[1],pcb_top]) washer();
}
module nut_fit_test() {
    sizes=[5.45,5.50,5.60,5.70,5.80,5.85];
    difference() {
        union() {
            cube([66,16,base_skin]);
            for(i=[0:len(sizes)-1]) {
                translate([6+11*i,11,0]) nut_support(sizes[i],nut_boss_height);
                translate([6+11*i,2.6,base_skin-eps]) linear_extrude(height=2*layer_height+eps)
                    text(str(sizes[i]),size=2.4,halign="center",valign="center",font="DejaVu Sans:style=Bold");
            }
        }
        for(i=[0:len(sizes)-1]) translate([6+11*i,11,0]) nut_pocket(sizes[i],nut_boss_height);
    }
}
