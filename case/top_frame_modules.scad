// Skeletal MX switch plate. Included by macropad_case.scad.
// Standard MX interface assumptions: plate top 5 mm above PCB, 14 mm apertures,
// 1.5 +/- 0.1 mm plate. Blue MX clones must be checked on the physical print.
// The switch's spring clips engage BELOW the plate; the flange rests ABOVE it.
// It is not a cover over the switch flange. Remove switches for installation.

/* [Minimal switch frame] */
frame_opening = 14.0;
frame_web = 1.2;
frame_reinforced = false;
frame_link_width = frame_reinforced ? 2.0 : 1.2;
frame_arm_width = frame_reinforced ? 2.4 : 1.6;
frame_thickness = 1.6;
frame_top = 5.0;
// Extra under-head screw length, relative to the chosen EXISTING base.
frame_screw_extra = 4.0;

/* [Hidden] */
frame_bottom = frame_top-frame_thickness;
// The original base height is preserved, but there are NO separate washers.
// Integral insulating feet touch the PCB. Recess the head 0.4 mm to use M3x10
// in the compact base, keeping the original tip and full nut engagement.
frame_screw_land = top_screw_land+frame_screw_extra;
frame_head_recess = frame_top-frame_screw_land;
frame_head_clearance_d = head_d+0.4;
frame_mount_d = frame_head_clearance_d+4*line_width;
frame_foot_d = washer_outer_d;

module frame_parameters() {
    assert(frame_opening>=14 && frame_opening<=14.2,"MX opening must remain close enough for the clips to engage");
    assert(frame_web>=3*line_width-0.000001 && frame_link_width>=3*line_width-0.000001,"Frame needs at least three extrusion lines");
    assert(frame_arm_width>=4*line_width-0.000001,"Mount arms need at least four extrusion lines");
    assert(frame_thickness>=1.4 && frame_thickness<=1.6,"MX clip plate must be 1.5 +/- 0.1 mm");
    assert(abs(frame_top-5)<0.001,"Standard MX plate top must be 5 mm above PCB");
    assert(frame_bottom>0,"Frame feet must fit above PCB");
    assert(frame_head_recess>=0 && frame_screw_land-frame_bottom>=minimum_bearing-0.000001,
           "Head recess must leave sufficient bearing above the foot");
    assert(abs(frame_thickness/layer_height-round(frame_thickness/layer_height))<0.001,
           "Frame thickness must be a whole number of print layers");
    echo(frame_plate=[frame_opening,frame_web,frame_thickness,frame_bottom,frame_top]);
    echo(frame_hardware=[screw_length,screw_length+frame_screw_extra,frame_screw_land,
                         frame_head_recess,frame_bottom]);
}

module frame_link(a,b,width) {
    hull() for(p=[a,b]) translate(p) circle(d=width);
}

// No perimeter rim and no crossbar behind the switches: leave the OLED exposed.
// Five short links join six collars; corner arms carry them to the four screws.
module frame_profile() {
    difference() {
        union() {
            for(p=pcb_key_centres) translate(p)
                offset(r=frame_web) square([frame_opening,frame_opening],center=true);
            for(pair=[[0,1],[1,2],[3,4],[4,5],[1,4]])
                frame_link(pcb_key_centres[pair[0]],pcb_key_centres[pair[1]],frame_link_width);
            // Attach at the outside corner of the nearest collar. Keeping rear
            // arms outboard avoids the OLED, its header and its support shelf.
            for(v=[[0,0,-1,1],[1,2,1,1],[2,3,-1,-1],[3,5,1,-1]])
                frame_link(pcb_mount_holes[v[0]],
                    [pcb_key_centres[v[1]][0]+v[2]*(frame_opening/2+frame_web/2),
                     pcb_key_centres[v[1]][1]+v[3]*(frame_opening/2+frame_web/2)],frame_arm_width);
            for(p=pcb_mount_holes) translate(p) circle(d=frame_mount_d);
        }
        for(p=pcb_key_centres) translate(p) square([frame_opening,frame_opening],center=true);
        for(p=pcb_mount_holes) translate(p) circle(d=screw_clearance_d);
    }
}

module top_frame() {
    frame_parameters();
    translate([0,0,pcb_top]) difference() {
        union() {
            translate([0,0,frame_bottom]) linear_extrude(height=frame_thickness) frame_profile();
            // Integral insulating feet replace the washers at the four mounts.
            for(p=pcb_mount_holes) translate([p[0],p[1],0])
                cylinder(d=frame_foot_d,h=frame_bottom+eps);
        }
        for(p=pcb_mount_holes) translate([p[0],p[1],-eps])
            cylinder(d=screw_clearance_d,h=frame_top+2*eps);
        for(p=pcb_mount_holes) translate([p[0],p[1],frame_screw_land])
            cylinder(d=frame_head_clearance_d,h=frame_head_recess+eps);
    }
}

module top_frame_print() {
    // Flat upper plate face on Z=0; the four integral feet point upwards.
    // Links start on the bed. Four 5.9 mm recess roofs use short bridges.
    translate([0,0,pcb_top+frame_top]) mirror([0,0,1]) top_frame();
}
