// Reinforced switch retaining frame. Included by macropad_case.scad.
// Prototype-fit revision: 14.0 x 14.75 mm openings, 6 mm feet, flat 1 mm plate.
// Clip engagement and key travel must be checked on the physical clone switches.
// Check housing/clip contact on the physical prototype. Remove switches to install.

/* [Reinforced switch frame] */
frame_opening = [14.0,14.75]; // X (left/right), Y (top/bottom); total aperture sizes.
frame_web = 1.2;
frame_link_width = 2.0;
frame_arm_width = 2.4;
frame_thickness = 1.0;
frame_standoff_height = 6.0;
frame_foot_wall = 0.8;
frame_top = frame_standoff_height+frame_thickness;
// Extra under-head screw length, relative to the chosen EXISTING base.
frame_screw_extra = 6.0;

/* [Hidden] */
frame_bottom = frame_standoff_height;
// The original base height is preserved, but there are NO separate washers.
// Screw heads bear on the flat upper face: no counterbores or bridged ceilings.
// M3x12 screws now have 2 mm nut engagement and 0.8 mm tip recess.
frame_screw_land = frame_top;
frame_screw_tip = pcb_top+frame_screw_land-screw_length-frame_screw_extra;
frame_thread_engagement = min(nut_height,nut_pocket_top-frame_screw_tip);
// Straight feet: 0.8 mm radial walls around the 3.4 mm bore, hence 5 mm OD.
frame_foot_d = screw_clearance_d+2*frame_foot_wall;
// The flat plate keeps a separate 6.2 mm screw pad above each straight foot.
frame_mount_d = head_d+0.7;
frame_bearing_height = frame_screw_land-frame_bottom;

module frame_parameters() {
    assert(len(frame_opening)==2 && min(frame_opening)>=14 && max(frame_opening)<=15.0,
           "Opening outside the prototype-fit range");
    assert(frame_web>=3*line_width-0.000001,"Collars need at least three extrusion lines");
    assert(frame_link_width>=5*line_width-0.000001,"Reinforced links need at least five extrusion lines");
    assert(frame_arm_width>=6*line_width-0.000001,"Reinforced arms need at least six extrusion lines");
    assert(frame_thickness>=1.0-0.000001 && frame_thickness<=1.6+0.000001,
           "Invalid frame thickness");
    assert(abs(frame_top-frame_bottom-frame_thickness)<0.001,"Plate height must match the standoff height plus its thickness");
    assert(frame_bottom>0,"Frame feet must fit above PCB");
    assert(frame_foot_wall>=2*line_width-0.000001,"Standoffs need at least two extrusion lines");
    assert(frame_mount_d>=head_d+0.5-0.000001,"Mount pad must support the whole screw head");
    assert(frame_foot_d<=frame_mount_d && (head_d-frame_foot_d)/2<=line_width+0.000001,
           "Excessive head bearing overhang beyond the standoff");
    assert(frame_screw_tip>=0 && frame_thread_engagement>=minimum_thread_engagement-0.000001,
           "Frame screws must engage the nuts without protruding below the base");
    assert(abs(frame_bottom/layer_height-round(frame_bottom/layer_height))<0.001,"Standoff height must be a whole number of print layers");
    assert(abs(frame_thickness/layer_height-round(frame_thickness/layer_height))<0.001,
           "Frame thickness must be a whole number of print layers");
    echo(frame_plate=[frame_opening,frame_web,frame_thickness,frame_bottom,frame_top]);
    echo(frame_hardware=[screw_length,screw_length+frame_screw_extra,frame_screw_land,
                         frame_screw_tip,frame_thread_engagement]);
    echo(frame_bearing=[frame_foot_d,frame_bearing_height,frame_foot_wall,frame_mount_d]);
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
                offset(delta=frame_web,chamfer=true) square(frame_opening,center=true);
            for(pair=[[0,1],[1,2],[3,4],[4,5],[1,4]])
                frame_link(pcb_key_centres[pair[0]],pcb_key_centres[pair[1]],frame_link_width);
            // Attach at the outside corner of the nearest collar. Keeping rear
            // arms outboard avoids the OLED, its header and its support shelf.
            for(v=[[0,0,-1,1],[1,2,1,1],[2,3,-1,-1],[3,5,1,-1]])
                frame_link(pcb_mount_holes[v[0]],
                    [pcb_key_centres[v[1]][0]+v[2]*(frame_opening[0]/2+frame_web/2),
                     pcb_key_centres[v[1]][1]+v[3]*(frame_opening[1]/2+frame_web/2)],frame_arm_width);
            for(p=pcb_mount_holes) translate(p) circle(d=frame_mount_d);
        }
        for(p=pcb_key_centres) translate(p) square(frame_opening,center=true);
        for(p=pcb_mount_holes) translate(p) circle(d=screw_clearance_d);
    }
}

module frame_foot() {
    cylinder(d=frame_foot_d,h=frame_bottom+eps);
}

module top_frame() {
    frame_parameters();
    translate([0,0,pcb_top]) difference() {
        union() {
            translate([0,0,frame_bottom]) linear_extrude(height=frame_thickness) frame_profile();
            // Integral insulating feet replace the washers at the four mounts.
            for(p=pcb_mount_holes) translate([p[0],p[1],0])
                frame_foot();
        }
        for(p=pcb_mount_holes) translate([p[0],p[1],-eps])
            cylinder(d=screw_clearance_d,h=frame_top+2*eps);
    }
}

module top_frame_print() {
    // Flat upper plate face on Z=0; the four integral feet point upwards.
    // The entire plate starts on the bed; straight feet rise from it. No bridges.
    translate([0,0,pcb_top+frame_top]) mirror([0,0,1]) top_frame();
}
