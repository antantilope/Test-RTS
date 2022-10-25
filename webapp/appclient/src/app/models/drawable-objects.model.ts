import { BoxCoords } from './box-coords.model';
import { PointCoord } from './point-coord.model';

export class DrawableShip {
    isSelf: boolean
    isDot?: boolean
    shipId: string
    alive: boolean
    mapCoord: PointCoord
    canvasCoordCenter: PointCoord
    designator: string
    inVisualRange: boolean
    visualEbeamCharging: boolean
    visualEbeamChargePercent: number
    visualEbeamFiring: boolean
    canvasBoundingBox: BoxCoords
    HBNoseMapCoord: PointCoord
    HBNoseCanvasCoord: PointCoord
    HBBottomLeftCanvasCoord: PointCoord
    HBBottomRightCanvasCoord: PointCoord
    HBBottomCenterCanvasCoord: PointCoord
    EngineOuterLeftCoord: PointCoord
    EngineInnerLeftCoord: PointCoord
    EngineOuterRightCoord: PointCoord
    EngineInnerRightCoord: PointCoord
    heading: number
    engineLit: boolean
    engineBoosted: boolean
    aflame: boolean
    exploded: boolean
    gravityBrakePosition: number
    gravityBrakeDeployedPosition: number
    gravityBrakeActive: boolean
    miningOreLocation: string
    fuelingAtStation:boolean
    lastTubeFireFrame: number
    distance?: number // this is missing when isSelf is true
}

export class DrawableMagnetMine {
    mineId: string
    isDot: boolean
    canvasCoordCenter: PointCoord
    canvasX1: number
    canvasY1: number
    canvasW: number
    canvasH: number
    canvasBoundingBox: BoxCoords
    percentArmed: number
    distance: number
}

export class DrawableEMP {
    EMPId: string
    isDot: boolean
    canvasCoordCenter: PointCoord
    canvasBoundingBox: BoxCoords
    radiusCanvasPX: number
    percentArmed: number
    distance: number
}

export class DrawableMagnetMineTargetingLine {
    mineCanvasCoord: PointCoord
    targetCanvasCoord: PointCoord
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
    magnetMines: DrawableMagnetMine[]
    magnetMineTargetingLines: DrawableMagnetMineTargetingLine[]
    emps: DrawableEMP[]
    ebeamRays: EBeamRayDetails[]
    mapWall?: BoxCoords
    visionCircles: VisionCircle[]
}
