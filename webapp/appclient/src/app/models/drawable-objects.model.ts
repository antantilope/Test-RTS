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
    visual_fill_color?: string
    visual_stroke_color?: string
    visual_line_width?: string
    distance?: number
    relative_heading?: number
    thermal_signature?: number
}

export class DrawableShip {
    isSelf: boolean
    canvasCoordCenter: PointCoord
    designator: string
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
    fillColor?: string
    strokeColor?: string
    lineWidth?: number
    distance?: number
    relativeHeading?: number
    thermalSignature?: number

}

export class DrawableReactionWheelOverlay {
    centerCanvasCoord: PointCoord
    radiusPx: number
    compassPoint0: PointCoord
    compassPoint1: PointCoord
}

export class DrawableEngineOverlay {
    vectorPoint0: PointCoord
    vectorPoint1: PointCoord
    metersPerSecond: number | string
}


export class DrawableCanvasItems {
    ships: DrawableShip[]
    reactionWheelOverlay?: DrawableReactionWheelOverlay
    engineOverlay?: DrawableEngineOverlay
}
