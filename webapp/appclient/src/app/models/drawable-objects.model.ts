import { BoxCoords } from './box-coords.model';
import { PointCoord } from './point-coord.model';

export class DrawableShip {
    isSelf: boolean
    isDot?: boolean
    shipId: string
    skinSlug: string
    alive: boolean
    mapCoord: PointCoord
    canvasCoordCenter: PointCoord
    designator: string
    inVisualRange: boolean
    visualEbeamChargePercent: number
    visualEbeamFiring: boolean
    canvasBoundingBox: BoxCoords
    HBNoseMapCoord: PointCoord
    HBBottomCenterMapCoord: PointCoord
    HBNoseCanvasCoord: PointCoord
    HBBottomLeftCanvasCoord: PointCoord
    HBBottomRightCanvasCoord: PointCoord
    HBBottomCenterCanvasCoord: PointCoord
    EngineOuterLeftCanvasCoord: PointCoord
    EngineInnerLeftCanvasCoord: PointCoord
    EngineOuterRightCanvasCoord: PointCoord
    EngineInnerRightCanvasCoord: PointCoord
    heading: number
    visualScannerMode: string | null
    visualScannerSensitivity: number | null
    visualScannerRangeMeters: number | null
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
    distance: number
}

export class DrawableHunterDrone {
    hunterDroneId: string
    isDot: boolean
    canvasCoordCenter: PointCoord
    canvasBoundingBox: BoxCoords
    percentArmed: number
    distance: number
    visualHeading: number
    isFriendly: boolean
    HBBottomCenterCanvasCoord: PointCoord
    HBBottomCenterMapCoord: PointCoord
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
    hunterDrones: DrawableHunterDrone[]
    ebeamRays: EBeamRayDetails[]
    mapWall?: BoxCoords
    visionCircles: VisionCircle[]
}
