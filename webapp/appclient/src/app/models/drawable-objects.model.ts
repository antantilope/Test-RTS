import { PointCoord } from './point-coord.model';


export class DrawableShip {
    canvasCoordP0: PointCoord
    canvasCoordP1: PointCoord
    canvasCoordP2: PointCoord
    canvasCoordP3: PointCoord
}


export class DrawableCanvasItems {
    ship?: DrawableShip;
}
