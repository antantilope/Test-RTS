import { BoxCoords } from './box-coords.model';
import { PointCoord } from './point-coord.model';

export class DrawableShip {
    isSelf: boolean
    isDot?: boolean
    shipId: string
    alive: boolean
    canvasCoordCenter: PointCoord
    designator: string
    inVisualRange: boolean
    canvasCoordP0: PointCoord
    canvasCoordP1: PointCoord
    canvasCoordP2: PointCoord
    canvasCoordP3: PointCoord
    visualEbeamCharging: boolean
    canvasCoordFin0P0: PointCoord
    canvasCoordFin0P1: PointCoord
    canvasCoordFin1P0: PointCoord
    canvasCoordFin1P1: PointCoord
    canvasBoundingBox: BoxCoords
    engineLit: boolean
    engineBoosted: boolean
    fillColor: string
    aflame: boolean
    exploded: boolean
    gravityBrakePosition: number
    gravityBrakeDeployedPosition: number
    gravityBrakeActive: boolean
    miningOreLocation: string
    fuelingAtStation:boolean
    lastTubeFireFrame: number
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
    ebeamRays: EBeamRayDetails[]
    mapWall?: BoxCoords
    visionCircles: VisionCircle[]
}
