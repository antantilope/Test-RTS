import { PointCoord } from './point-coord.model';


export class DrawableShip {
    canvasCoordP0: PointCoord
    canvasCoordP1: PointCoord
    canvasCoordP2: PointCoord
    canvasCoordP3: PointCoord
    canvasCoordCenter: PointCoord
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
    ship?: DrawableShip
    reactionWheelOverlay?: DrawableReactionWheelOverlay
    engineOverlay?: DrawableEngineOverlay
}
