import { BoxCoords } from './box-coords.model';
import { PointCoord } from './point-coord.model';

export class ScannerDataElement {
    /*
        Data returned from the server representing
        an object that has been picked up by the scanner
    */
    element_type: string
    coord_x: number
    coord_y: number
    id: string
    alive: boolean
    designator: string
    visual_shape?: string
    visual_p0?: number[]
    visual_p1?: number[]
    visual_p2?: number[]
    visual_p3?: number[]
    visual_fin_0_rel_rot_coord_0?: number[]
    visual_fin_0_rel_rot_coord_1?: number[]
    visual_fin_1_rel_rot_coord_0?: number[]
    visual_fin_1_rel_rot_coord_1?: number[]
    visual_engine_lit?: boolean
    visual_engine_boosted_last_frame?: number
    visual_fill_color?: string
    visual_stroke_color?: string
    visual_line_width?: string
    aflame?: boolean
    explosion_frame?: number
    distance?: number
    relative_heading?: number
    thermal_signature?: number
    visual_gravity_brake_position?: number
    visual_gravity_brake_deployed_position?: number
    visual_gravity_brake_active?: boolean
}

export class DrawableShip {
    isSelf: boolean
    isDot?: boolean
    shipId: string
    alive: boolean
    canvasCoordCenter: PointCoord
    designator: string
    isVisual: boolean
    canvasCoordP0?: PointCoord
    canvasCoordP1?: PointCoord
    canvasCoordP2?: PointCoord
    canvasCoordP3?: PointCoord
    canvasCoordFin0P0?: PointCoord
    canvasCoordFin0P1?: PointCoord
    canvasCoordFin1P0?: PointCoord
    canvasCoordFin1P1?: PointCoord
    canvasBoundingBox?: BoxCoords
    engineLit?: boolean
    engineBoosted?: boolean
    fillColor?: string
    strokeColor?: string
    lineWidth?: number
    distance?: number
    relativeHeading?: number
    thermalSignature?: number
    aflame?: boolean
    explosionFrame?: number
    gravityBrakePosition?: number
    gravityBrakeDeployedPosition?: number
    gravityBrakeActive?: boolean
}

export class EBeamRayDetails {
    startPoint: PointCoord
    endPoint: PointCoord
    color: string
}


export class VisionCircle {
    canvasCoord: PointCoord
    radius: number
    color: string
    name: string
}


export class DrawableCanvasItems {
    ships: DrawableShip[]
    ebeamRays: EBeamRayDetails[]
    mapWall?: BoxCoords
    visionCircles: VisionCircle[]
}
