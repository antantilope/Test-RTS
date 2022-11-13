import { Injectable } from '@angular/core';

import { ApiService } from './api.service';
import {
  Camera,
  VelocityTrailElement,
  FlameSmokeElement,
  EMPTrailElement,
  VELOCITY_TRAIL_ELEMENT_TTL_MS,
  FLAME_SMOKE_ELEMENT_TTL_MS,
  EMP_TRAIL_ELEMENT_TTL_MS,
  EBeamFiringEffectElement,
  EBEAM_EFFECT_ELEMENT_TTL_MS,
  GravityBrakeShipEffectElement,
  GRAVITY_BREAK_SHIP_EFFECT_ELEMENT_TTL_MS,
  CameraService,
} from './camera.service';
import { FormattingService } from './formatting.service';
import { QuoteService, QuoteDetails } from './quote.service';
import { UserService } from "./user.service";
import { AssetService } from './asset.service';
import {
  BoxCoords
} from "./models/box-coords.model"
import {
  DrawableShip,
  DrawableMagnetMine,
  DrawableMagnetMineTargetingLine,
  DrawableEMP,
  DrawableHunterDrone,
  VisionCircle,
  EBeamRayDetails,
} from "./models/drawable-objects.model"
import { TimerItem } from './models/timer-item.model';
import { PointCoord } from './models/point-coord.model';
import {
  TWO_PI,
  PI_OVER_180,
  LOW_FUEL_THRESHOLD,
  LOW_POWER_THRESHOLD,
  SHIP_LENGTH_METERS_X,
  SHIP_LENGTH_METERS_Y,
  HUNTER_DRONE_LENGTH_METERS_X,
  HUNTER_DRONE_LENGTH_METERS_Y,
  STATION_LENGTH_METERS_X,
  STATION_LENGTH_METERS_Y,
  TIMER_SLUG_SCANNER_LOCKING,
} from './constants';
import { Explosion, OreMine, EMPBlast, SpaceStation } from './models/apidata.model';




const randomInt = function (min: number, max: number): number  {
  return Math.floor(Math.random() * (max - min) + min)
}

function getRandomFloat(min: number, max: number): number {
  return Math.random() * (max - min) + min;
}

function nthRoot(x, root) {
  return Math.pow(x, 1 / root)
}

const simpleHash = (str, maxInt) => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash &= hash;
  }
  return Math.abs(hash) % maxInt
};

class BottomRightOverlaySizing {
  yInterval: number
  timerRightXOffset: number
  timerLabelFontSize: number
  timerBarHeight: number
  timerBarLen: number
  gameClockFontSize: number
  XCornerOffset: number
  YCornerOffset: number
  clockTimerGap: number
}

class TopLeftOverlaySizing {
  xCornerOffset: number
  yCornerOffset: number
  fontSize: number
  yInterval: number
}

class FrontAndCenterAlertSizing {
  victoryTextFontSize: number
  victoryTextYTopOffset: number
  gameOverFontSize: number
  gameOverYTopOffset: number
  deathQuoteFontSize: number
  deathQuoteYTopOffset: number
  deathQuoteYInterval: number
  deathQuoteXOffset: number
  abbreviateDockedAt: boolean
  dockedAtFontSize: number
  docketAtYTopOffset: number
  dockedAtYInterval?: number
}

@Injectable({
  providedIn: 'root'
})
export class DrawingService {

  private isCinematic = window.location.search.indexOf("cinematic") !== -1
  private isDebug = window.location.search.indexOf("debug") !== -1

  private deathQuote: QuoteDetails | null = null;

  private maxLockingModLength = 30
  private lockingCounter = 0
  private minOnCount = 10
  private onForCount = 0

  private nameHashes: Map<string, number> = new Map()

  constructor(
    private _camera: CameraService,
    private _api: ApiService,
    private _formatting: FormattingService,
    private _quote: QuoteService,
    public _user: UserService,
    private _asset: AssetService,
  ) {
    this.deathQuote = this._quote.getQuote()
  }

  private getNameHash(name: string): number {
    if (this.nameHashes.has(name)) {
      return this.nameHashes.get(name)
    }
    const hash = simpleHash(name, 5000)
    this.nameHashes.set(name, hash)
    return hash
  }

  public drawMapBoundary(
    ctx: CanvasRenderingContext2D,
    camera: Camera,
    mapWallCanvasBoxCoords: BoxCoords,
  ) {
    ctx.beginPath()
    ctx.strokeStyle ="#5e5e00"
    ctx.lineWidth = Math.max(
      2,
      Math.ceil(8 * this._api.frameData.map_config.units_per_meter / camera.getZoom()),
    )
    ctx.rect(
      mapWallCanvasBoxCoords.x1,
      mapWallCanvasBoxCoords.y1,
      mapWallCanvasBoxCoords.x2 - mapWallCanvasBoxCoords.x1,
      mapWallCanvasBoxCoords.y2 - mapWallCanvasBoxCoords.y1,
    )
    ctx.stroke()
  }

  public drawVisionCircles(
    ctx: CanvasRenderingContext2D,
    visionCircles: VisionCircle[],
  ) {
    for(let i in visionCircles) {
      let vs = visionCircles[i]
      const isRadar = vs.name === "radar"
      let endRad: number
      let startRad: number
      if(isRadar) {
        const sensitivity = this._api.frameData.ship.scanner_radar_sensitivity
        const rate = 30// {0:30, 1:20, 2:14, 3:8}[sensitivity]
        const percent = (this._api.frameData.game_frame % rate) / rate
        endRad = TWO_PI * percent
        startRad = endRad - (Math.PI - (Math.PI / randomInt(1, 4)))
      } else {
        startRad = 0
        endRad = TWO_PI
      }
      ctx.beginPath()
      ctx.fillStyle = vs.color
      ctx.arc(
        vs.canvasCoord.x,
        vs.canvasCoord.y,
        vs.radius,
        startRad,
        endRad,
      )
      ctx.fill()
    }
  }

  public drawVisualVelocityElements(
    ctx: CanvasRenderingContext2D,
    camera: Camera,
    velocityTrailElements: VelocityTrailElement[],
  ) {
    if(this.isCinematic) {
      return
    }
    const cameraPosition = camera.getPosition()
    const now = performance.now()
    for(let i in velocityTrailElements) {
      let vte = velocityTrailElements[i]
      let alpha = (VELOCITY_TRAIL_ELEMENT_TTL_MS - (now - vte.createdAt)) / VELOCITY_TRAIL_ELEMENT_TTL_MS
      let pixelRadius = Math.max(
        2,
        vte.radiusMeters * this._api.frameData.map_config.units_per_meter / camera.getZoom(),
      ) * (vte.grow ? (1 + (3 * (now - vte.createdAt) / VELOCITY_TRAIL_ELEMENT_TTL_MS)): 1) // grow arc to 3x size if grow==true
      let canvasCoord = camera.mapCoordToCanvasCoord(vte.mapCoord, cameraPosition)
      ctx.beginPath()
      ctx.fillStyle = `rgb(140, 140, 140, ${alpha})`
      ctx.arc(canvasCoord.x, canvasCoord.y, pixelRadius, 0, TWO_PI)
      ctx.fill()
    }
  }

  public drawVisualFlameSmokeElements(
    ctx: CanvasRenderingContext2D,
    camera: Camera,
    flameSmokeElements: FlameSmokeElement[],
  ){
    const cameraPosition = camera.getPosition()
    const zoom = camera.getZoom()
    const ppm = this._api.frameData.map_config.units_per_meter
    const now = performance.now()
    const maxGrowthCoef = 1.9
    for(let i in flameSmokeElements) {
      let fse = flameSmokeElements[i]
      let agePercent = (now - fse.createdAt) / FLAME_SMOKE_ELEMENT_TTL_MS
      let radiusPx = (fse.initalRadiusMeters + (fse.initalRadiusMeters * maxGrowthCoef * agePercent)) * ppm / zoom
      let alpha = 0.55 - (0.55 * agePercent)
      let canvasCoord = camera.mapCoordToCanvasCoord(fse.mapCoord, cameraPosition)
      ctx.beginPath()
      ctx.fillStyle = `rgb(127, 127, 127, ${alpha})`
      ctx.arc(
        canvasCoord.x, canvasCoord.y,
        radiusPx, 0, TWO_PI
      )
      ctx.fill()
    }
  }

  public drawEMPTrailElements(
    ctx: CanvasRenderingContext2D,
    camera: Camera,
    EMPTrailElements: EMPTrailElement[],
  ){
    const cameraPosition = camera.getPosition()
    const zoom = camera.getZoom()
    const ppm = this._api.frameData.map_config.units_per_meter
    const now = performance.now()
    const maxGrowthCoef = 3.5
    for(let i in EMPTrailElements) {
      let empTE = EMPTrailElements[i]
      let agePercent = (now - empTE.createdAt) / EMP_TRAIL_ELEMENT_TTL_MS
      let radiusPx = (empTE.initalRadiusMeters + (empTE.initalRadiusMeters * maxGrowthCoef * agePercent)) * ppm / zoom
      let alpha = 0.55 - (0.55 * agePercent)
      let canvasCoord = camera.mapCoordToCanvasCoord(empTE.mapCoord, cameraPosition)
      ctx.beginPath()
      ctx.fillStyle = `rgb(0, 0, 255, ${alpha})`
      ctx.arc(
        canvasCoord.x, canvasCoord.y,
        radiusPx, 0, TWO_PI
      )
      ctx.fill()
    }
  }

  public drawOreDepositEffect(
    ctx: CanvasRenderingContext2D,
    camera: Camera,
  ) {
    const effectLengthFrames = 30
    if (
      (
        (this._api.frameData.ship.last_ore_deposit_frame + effectLengthFrames)
        < this._api.frameData.game_frame
      )
      || this._api.frameData.game_frame < 100
    ) {
      return
    }
    const ship = this._api.frameData.ship
    const effectFrame = (
      this._api.frameData.game_frame
      - ship.last_ore_deposit_frame
    )

    const shipCanvasCoords = camera.mapCoordToCanvasCoord(
      {x: ship.coord_x, y: ship.coord_y},
      camera.getPosition(),
    )

    const effectRadius = (15 + effectFrame) * 3.5
    const alpha = 0.5 - (effectFrame * 0.015)
    ctx.beginPath()
    ctx.fillStyle = `rgb(255, 255, 0, ${alpha})`
    ctx.arc(
      shipCanvasCoords.x,
      shipCanvasCoords.y,
      effectRadius, 0, TWO_PI,
    )
    ctx.fill()

    const offset = effectLengthFrames - (effectFrame + 1)
    let textCoord = {
      x:shipCanvasCoords.x + 40 + offset,
      y:shipCanvasCoords.y - 40 - offset
    }
    ctx.beginPath()
    ctx.font = '30px Courier New'
    ctx.fillStyle = `rgb(255, 255, 0, ${alpha * 1.25})`
    ctx.fillText("🪙", textCoord.x, textCoord.y)
  }

  public drawWaypoint(
    ctx: CanvasRenderingContext2D,
    camera: Camera,
    wayPointMapCoord: PointCoord
  ) {
    const ship = this._api.frameData.ship
    if(!ship.alive) {
      return
    }

    const cameraPosition = camera.getPosition()
    let wpCanvasCoord = camera.mapCoordToCanvasCoord(
      wayPointMapCoord, cameraPosition
    )
    let shipCanvasCoord = camera.mapCoordToCanvasCoord(
      {x: ship.coord_x, y: ship.coord_y}, cameraPosition
    )

    // Draw line
    ctx.beginPath()
    ctx.strokeStyle = "rgb(144, 0, 173, 0.5)"
    ctx.lineWidth = 2
    ctx.setLineDash([5, 10]);
    ctx.moveTo(shipCanvasCoord.x, shipCanvasCoord.y)
    ctx.lineTo(wpCanvasCoord.x, wpCanvasCoord.y)
    ctx.stroke()
    ctx.setLineDash([]);
    // Draw flag pole
    const poleHeight = 38
    const flagHeight = 10
    const flagWidth = 12
    ctx.beginPath()
    ctx.fillStyle = "rgb(144, 0, 173, 0.75)"
    ctx.strokeStyle = "rgb(144, 0, 173, 0.75)"
    ctx.moveTo(wpCanvasCoord.x, wpCanvasCoord.y)
    ctx.lineTo(wpCanvasCoord.x, wpCanvasCoord.y - poleHeight)
    ctx.stroke()
    // Draw flag
    ctx.moveTo(wpCanvasCoord.x, wpCanvasCoord.y - poleHeight)
    ctx.lineTo(wpCanvasCoord.x + flagWidth, wpCanvasCoord.y - (poleHeight - flagHeight / 2))
    ctx.lineTo(wpCanvasCoord.x, wpCanvasCoord.y - (poleHeight - flagHeight))
    ctx.closePath()
    ctx.fill()
  }

  public drawVelocityAndHeadingLine(
    ctx: CanvasRenderingContext2D,
    camera: Camera,
    visionCircle: VisionCircle,
    headingOnly: boolean = false, // FIXME: garbage parameter.
  ) {
    const alpha = getRandomFloat(0.2, 0.6)
    const ship = this._api.frameData.ship
    if(!ship.alive) {
      return
    }
    // Draw Velocity line if there is any velocity
    if(
      !headingOnly && (ship.velocity_x_meters_per_second !== 0
      || ship.velocity_y_meters_per_second !== 0)
    ) {
      const vAngleRads = camera.getCanvasAngleBetween(
        {x:0, y:0},
        {
          x: visionCircle.canvasCoord.x + ship.velocity_x_meters_per_second * 1000,
          y: visionCircle.canvasCoord.y + ship.velocity_y_meters_per_second * 1000,
        }
      ) * (Math.PI / 180)
      const velocityLinePointB = {
        x: visionCircle.canvasCoord.x + (visionCircle.radius * Math.sin(vAngleRads)),
        y: visionCircle.canvasCoord.y + (visionCircle.radius * Math.cos(vAngleRads)),
      }
      ctx.beginPath()
      ctx.lineWidth = 2
      ctx.strokeStyle = `rgb(144, 0, 173, ${alpha})`
      ctx.moveTo(visionCircle.canvasCoord.x, visionCircle.canvasCoord.y)
      ctx.lineTo(velocityLinePointB.x, velocityLinePointB.y)
      ctx.stroke()

      ctx.beginPath()
      ctx.fillStyle = `rgb(144, 0, 173, ${alpha})`
      ctx.arc(velocityLinePointB.x, velocityLinePointB.y, 8, 0, TWO_PI)
      ctx.fill()
    }

    // Draw heading line
    const hAngleRads = (180 - ship.heading) * PI_OVER_180 // why -180? because it works.
    const headingLinePointB = {
      x: visionCircle.canvasCoord.x + (visionCircle.radius * Math.sin(hAngleRads)),
      y: visionCircle.canvasCoord.y + (visionCircle.radius * Math.cos(hAngleRads)),
    }
    ctx.beginPath()
    ctx.lineWidth = 2
    ctx.strokeStyle = `rgb(144, 0, 173, ${alpha})`
    ctx.moveTo(visionCircle.canvasCoord.x, visionCircle.canvasCoord.y)
    ctx.lineTo(headingLinePointB.x, headingLinePointB.y)
    ctx.stroke()
  }

  public drawLineToScannerCursor(
    ctx: CanvasRenderingContext2D,
    camera: Camera,
    scannerTargetID: string,
  ) {
    if(Math.random() < 0.5) {
      return
    }
    const target = this._api.frameData.ship.scanner_ship_data.find(
      sde=>sde.id === scannerTargetID)
    if(!target) {
      return
    }
    const cameraPosition = camera.getPosition()
    const alpha = getRandomFloat(0.2, 0.6)
    const pointA = camera.mapCoordToCanvasCoord(
      {x:this._api.frameData.ship.coord_x, y:this._api.frameData.ship.coord_y},
      cameraPosition,
    )
    const pointB = camera.mapCoordToCanvasCoord(
      {x:target.coord_x, y:target.coord_y},
      cameraPosition,
    )
    ctx.beginPath()
    ctx.lineWidth = 2
    ctx.strokeStyle = `rgb(190, 0, 0,  ${alpha})`
    ctx.moveTo(pointA.x, pointA.y)
    ctx.lineTo(pointB.x, pointB.y)
    ctx.stroke()
  }

  public drawEbeams(
    ctx: CanvasRenderingContext2D,
    camera: Camera,
    rays: EBeamRayDetails[],
  ) {
    const ebeamThickness = Math.max(3, 1.15 * this._api.frameData.map_config.units_per_meter / camera.getZoom())
    for(let i in rays) {
      let ray = rays[i]
      ctx.beginPath()
      ctx.strokeStyle = ray.color
      ctx.lineWidth = ebeamThickness
      ctx.moveTo(ray.startPoint.x, ray.startPoint.y)
      ctx.lineTo(ray.endPoint.x, ray.endPoint.y)
      ctx.stroke()
    }
  }

  public drawEBeamFiringEffectElements(
    ctx: CanvasRenderingContext2D,
    camera: Camera,
    elements: EBeamFiringEffectElement[],
  ) {
    if(!elements.length) {
      return
    }
    const now = performance.now()
    const cameraPosition = camera.getPosition()
    const zoom = camera.getZoom()
    for(let i in elements) {
      let el = elements[i]
      let percentAge = (now - el.createdAt) / EBEAM_EFFECT_ELEMENT_TTL_MS
      if(percentAge >= 1){
        continue
      }
      let alpha = 0.1 * (1 - percentAge)
      let radiusPx = (1 + 10 * percentAge) * this._api.frameData.map_config.units_per_meter / zoom
      let cc = camera.mapCoordToCanvasCoord(el.mapCoord, cameraPosition)
      let nonRedIntensity = Math.floor(255 * percentAge)
      ctx.beginPath()
      ctx.fillStyle = `rgb(255, ${nonRedIntensity}, ${nonRedIntensity}, ${alpha})`
      ctx.arc(
        cc.x, cc.y, radiusPx, 0, TWO_PI
      )
      ctx.fill()
    }
  }

  private getBottomRightOverlay(canvasW: number, canvasH: number): BottomRightOverlaySizing{
    if(canvasW >= 650 && canvasH >= 450) {
      // "larger" screen sizing
      return {
        yInterval: 45,
        clockTimerGap: 55,
        gameClockFontSize: 28,
        XCornerOffset: 15,
        YCornerOffset: 15,

        timerBarLen: 200,
        timerRightXOffset: 15,
        timerLabelFontSize: 28,
        timerBarHeight: 30,
      }
    } else {
      // "smaller" screen sizing
      return {
        yInterval: 25,
        clockTimerGap: 35,
        gameClockFontSize: 19,
        XCornerOffset: 5,
        YCornerOffset: 5,
        timerBarLen: 105,
        timerRightXOffset: 5,
        timerLabelFontSize: 18,
        timerBarHeight: 20,
      }
    }
  }

  public drawBottomRightOverlay(
    ctx: CanvasRenderingContext2D,
    camera: Camera,
  ) {
    // This method is a bit of a mess
    const sizing = this.getBottomRightOverlay(camera.canvasWidth, camera.canvasHeight)
    let brcYOffset = sizing.YCornerOffset
    // Game Time
    ctx.strokeStyle = '#ffffff'
    ctx.fillStyle = '#ffffff'
    ctx.lineWidth = 1
    ctx.textAlign = 'right'
    ctx.textBaseline = "bottom"
    ctx.font = `bold ${sizing.gameClockFontSize}px Courier New`
    ctx.beginPath()
    ctx.fillText(
      this._api.frameData.elapsed_time,
      camera.canvasWidth - sizing.XCornerOffset,
      camera.canvasHeight - brcYOffset,
    )

    // Timers
    const timerBarLength = sizing.timerBarLen //Math.min(200, Math.round(camera.canvasWidth / 6.5))
    const brcXOffset = sizing.timerRightXOffset
    const textRAlignXOffset = brcXOffset + timerBarLength + 10
    const barRAlignXOffset = brcXOffset + timerBarLength
    if(this._api.frameData.ship.alive){
      ctx.font = `${sizing.timerLabelFontSize}px Courier New`
      ctx.strokeStyle = '#00ff00'
      brcYOffset += sizing.clockTimerGap
      ctx.textBaseline = "middle"
      ctx.textAlign = "right"
      for(let i in this._api.frameData.ship.timers) {
        const timer: TimerItem = this._api.frameData.ship.timers[i]
        const fillLength = Math.round((timer.percent / 100) * timerBarLength)
        ctx.beginPath()
        ctx.fillStyle = '#006600'
        ctx.rect(
          camera.canvasWidth - barRAlignXOffset, // top left x
          camera.canvasHeight - (brcYOffset + sizing.timerBarHeight / 2), // top left y
          timerBarLength,       // widthc
          sizing.timerBarHeight,// height
        )
        ctx.stroke()
        ctx.beginPath()
        ctx.rect(
          camera.canvasWidth - barRAlignXOffset, // top left x
          camera.canvasHeight - (brcYOffset + sizing.timerBarHeight / 2),  // top left y
          fillLength,            // width
          sizing.timerBarHeight, // height
        )
        ctx.fill()
        ctx.beginPath()
        ctx.fillStyle = '#ffffff'
        ctx.fillText(
          timer.name.toLocaleLowerCase(),
          camera.canvasWidth - (sizing.timerRightXOffset + 2),
          camera.canvasHeight - (brcYOffset),
        )
        brcYOffset += sizing.yInterval
      }
    }
  }

  private getTopLeftOverlaySizing(canvasW: number, canvasH: number): TopLeftOverlaySizing {
    if(canvasW >= 650 && canvasH >= 450) {
      return {
        xCornerOffset: 15,
        yCornerOffset: 25,
        fontSize: 24,
        yInterval: 34,
      }
    } else {
      return {
        xCornerOffset: 9,
        yCornerOffset: 15,
        fontSize: 18,
        yInterval: 24,
      }
    }
  }

  public drawTopLeftOverlay(
    ctx: CanvasRenderingContext2D,
    cameraMode: string,
    camera: Camera,
  ) {
    if(!this._api.frameData || !this._api.frameData.ship.alive) {
      return
    }
    const sizing = this.getTopLeftOverlaySizing(
      camera.canvasWidth,
      camera.canvasHeight,
    )
    let tlcYOffset = sizing.yCornerOffset
    const tlcXOffset = sizing.xCornerOffset
    // Fuel amount
    ctx.beginPath()
    ctx.font = `${sizing.fontSize}px Courier New`
    ctx.fillStyle = '#ff9494'
    ctx.textAlign = 'left'
    ctx.textBaseline = 'middle'
    ctx.fillText("⛽" + this._formatting.formatNumber(this._api.frameData.ship.fuel_level), tlcXOffset, tlcYOffset)
    tlcYOffset += sizing.yInterval

    // Battery amount
    ctx.beginPath()
    ctx.fillStyle = '#98ffbe'
    ctx.fillText("🔋" + this._formatting.formatNumber(this._api.frameData.ship.battery_power), tlcXOffset, tlcYOffset)
    tlcYOffset += sizing.yInterval

    // Ore amount
    const realOreKg = this._formatting.formatNumber(this._api.frameData.ship.cargo_ore_mass_kg)
    const virtualOreKg = this._formatting.formatNumber(this._api.frameData.ship.virtual_ore_kg)
    ctx.beginPath()
    ctx.fillStyle = '#fffa65'
    ctx.fillText(`💎${realOreKg} 🪙${virtualOreKg}`, tlcXOffset, tlcYOffset)
    tlcYOffset += sizing.yInterval

    // Speed
    const velocityMS = Math.sqrt(
      Math.pow(this._api.frameData.ship.velocity_x_meters_per_second, 2)
      + Math.pow(this._api.frameData.ship.velocity_y_meters_per_second, 2)
    ).toFixed(0)
    ctx.beginPath()
    ctx.fillStyle = '#ffcccc'
    ctx.fillText(`💨 ${velocityMS} M/S`, tlcXOffset, tlcYOffset)
    tlcYOffset += sizing.yInterval

    // Thermal signature
    ctx.beginPath()
    ctx.fillStyle = '#ffcccc'
    ctx.fillText(`🌡️ ${this._api.frameData.ship.scanner_thermal_signature}`, tlcXOffset, tlcYOffset)
    tlcYOffset += sizing.yInterval

    // Camera mode
    ctx.beginPath()
    ctx.fillStyle = '#ffcccc'
    ctx.fillText("🎥 " + cameraMode.toUpperCase(), tlcXOffset, tlcYOffset)
    tlcYOffset += sizing.yInterval
  }

  public drawBottomLeftOverlay(
    ctx: CanvasRenderingContext2D,
    camera: Camera,
    isCameraModeMap: boolean,
    pneumaticWeaponMsg: string,
  ) {
    let lrcYOffset = camera.canvasHeight - 30
    let lrcYInterval = 40
    const lrcXOffset = 15
    // Scale Bar
    const barLengthMeters = (
      (
        (camera.canvasWidth / 4)
        * camera.getZoom()
      )
      / this._api.frameData.map_config.units_per_meter
    )
    let scaleLabel;
    if(barLengthMeters >= 5000) {
      scaleLabel = (barLengthMeters / 1000).toFixed(2) + " KM"
    }
    else {
      scaleLabel = Math.round(barLengthMeters) + " Meters"
    }
    ctx.beginPath()
    ctx.strokeStyle = "#ffffff"
    ctx.lineWidth = 3
    ctx.moveTo(lrcXOffset, lrcYOffset);
    ctx.lineTo((camera.canvasWidth / 4) + lrcXOffset, lrcYOffset);
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(lrcXOffset, lrcYOffset);
    ctx.lineTo( lrcXOffset, lrcYOffset - 10);
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo((camera.canvasWidth / 4) + lrcXOffset, lrcYOffset);
    ctx.lineTo((camera.canvasWidth / 4) + lrcXOffset, lrcYOffset - 10);
    ctx.stroke()
    // Scale meters and user handle
    ctx.beginPath()
    ctx.font = '24px serif'
    ctx.fillStyle = this._api.frameData.ship.alive ? '#ffffff' : "#ff0000";
    ctx.textAlign = 'left'
    ctx.fillText(scaleLabel, lrcXOffset + 8, lrcYOffset - 12)
    if(isCameraModeMap) {
      return
    }
    lrcYOffset -= lrcYInterval
    ctx.beginPath()
    ctx.font = '20px Courier New'
    ctx.fillText("Ensign " + this._user.handle, lrcXOffset, lrcYOffset)
    lrcYOffset -= lrcYInterval
    // Red alerts
    if(this._api.frameData.ship.alive) {
      lrcYInterval = 30
      ctx.font = 'bold 22px courier new'
      const redalertColorAlpha = this._api.frameData.game_frame % 70 > 35 ? "1" : "0.65"
      ctx.fillStyle = `rgb(255, 2, 2, ${redalertColorAlpha})`
      if(this._api.frameData.ship.fuel_level < LOW_FUEL_THRESHOLD) {
        ctx.beginPath()
        ctx.fillText("⚠️ LOW FUEL", lrcXOffset, lrcYOffset)
        lrcYOffset -= lrcYInterval + 5
      }
      if(this._api.frameData.ship.battery_power < LOW_POWER_THRESHOLD) {
        ctx.beginPath()
        ctx.fillText("⚠️ LOW POWER", lrcXOffset, lrcYOffset)
        lrcYOffset -= lrcYInterval + 5
      }

      // Selected Pneumatic Weapon
      ctx.beginPath()
      ctx.fillStyle = "#ffffff"
      ctx.font = 'bold 22px Courier New'
      ctx.fillText(pneumaticWeaponMsg, lrcXOffset, lrcYOffset)
      lrcYOffset -= lrcYInterval

      if (this._api.frameData.ship.engine_lit) {
        ctx.drawImage(
          this._asset.actionTileImgEngineLit,
          lrcXOffset,
          lrcYOffset - 100,
          100, 100,
        )
        lrcYOffset -= 120
      }
      else if (this._api.frameData.ship.engine_online || this._api.frameData.ship.engine_starting) {
        ctx.drawImage(
          this._asset.actionTileImgEngineOnline,
          lrcXOffset,
          lrcYOffset - 100,
          100, 100,
        )
        lrcYOffset -= 120
      }
      if(this._api.frameData.ship.scanner_online || this._api.frameData.ship.scanner_starting) {
        ctx.drawImage(
          this._asset.actionTileImgScannerOnline,
          lrcXOffset,
          lrcYOffset - 100,
          100, 100,
        )
        lrcYOffset -= 120
      }
    }
  }

  private getFrontAndCenterAlertsSizing(canvasW: number, canvasH: number): FrontAndCenterAlertSizing {
    if(canvasW > 650 && canvasH >= 450) {
      return {
        victoryTextFontSize: 65,
        victoryTextYTopOffset: Math.floor(canvasH / 4),
        gameOverFontSize: 56,
        gameOverYTopOffset: Math.floor(canvasH / 8),
        deathQuoteFontSize: 35,
        deathQuoteYTopOffset: 50,
        deathQuoteYInterval: 40,
        deathQuoteXOffset: 50,
        abbreviateDockedAt: false,
        dockedAtFontSize: 32,
        dockedAtYInterval: 45,
        docketAtYTopOffset: 50,
      }
    } else {
      return {
        victoryTextFontSize: 45,
        victoryTextYTopOffset: Math.floor(canvasH / 4),
        gameOverFontSize: 40,
        gameOverYTopOffset: Math.floor(canvasH / 7),
        deathQuoteFontSize: 18,
        deathQuoteYTopOffset: 50,
        deathQuoteYInterval: 20,
        deathQuoteXOffset: 10,
        abbreviateDockedAt: true,
        docketAtYTopOffset: 20,
        dockedAtFontSize: 25,
      }
    }
  }

  public drawFrontAndCenterAlerts(
    ctx: CanvasRenderingContext2D,
    camera: Camera,
  ) {
    // This function executes 1 if block and NOTHING MORE. (some have return statements.)
    const sizing = this.getFrontAndCenterAlertsSizing(camera.canvasWidth, camera.canvasHeight)
    if (this._api.frameData.winning_team == this._api.frameData.ship.team_id) {
      ctx.beginPath()
      ctx.font = `bold ${sizing.victoryTextFontSize}px courier new`
      ctx.fillStyle = '#ffffff'
      ctx.textAlign = 'center'
      ctx.fillText("🏆VICTORY", camera.canvasHalfWidth, sizing.victoryTextYTopOffset)
    }
    else if(!this._api.frameData.ship.alive) {
      if((this._api.frameData.ship.died_on_frame + 100) > this._api.frameData.game_frame) {
        // delay showing death quote
        return;
      }
      ctx.beginPath()
      ctx.font = `bold ${sizing.gameOverFontSize}px courier new`
      ctx.fillStyle = '#ff0000'
      ctx.textAlign = 'left'
      let deathTextYOffset = sizing.gameOverYTopOffset
      const deathQuoteInterval = sizing.deathQuoteYInterval
      if(this._api.frameData.game_frame % 50 > 25) {
        ctx.fillText("GAME OVER", sizing.deathQuoteXOffset, deathTextYOffset)
      }
      deathTextYOffset += (deathQuoteInterval * 2)
      ctx.beginPath()
      ctx.fillStyle = '#b8b8b8' // medium light gray
      ctx.textAlign = 'left'
      ctx.font = `bold ${sizing.deathQuoteFontSize}px Verdana`
      for(let i in this.deathQuote.lines) {
        const prefix = parseInt(i) === 0 ? '"' : ""
        ctx.fillText(prefix + this.deathQuote.lines[i], sizing.deathQuoteXOffset, deathTextYOffset)
        deathTextYOffset += deathQuoteInterval
      }
      deathTextYOffset += deathQuoteInterval * 0.5
      ctx.beginPath()
      ctx.font = `italic ${Math.floor(0.95*sizing.deathQuoteFontSize)}px Verdana`
      ctx.fillText((this.deathQuote.author || "Unknown"),
        sizing.deathQuoteXOffset,
        deathTextYOffset)
    }
    else if(this._api.frameData.ship.docked_at_station) {
      if(sizing.abbreviateDockedAt) {
        ctx.beginPath()
        ctx.font = `bold ${sizing.dockedAtFontSize}px courier new`
        ctx.fillStyle = '#00ff00'
        ctx.textAlign = 'center'
        ctx.fillText(
          "Docked🛰️",
          camera.canvasHalfWidth,
          sizing.docketAtYTopOffset
        )
      }else {
        const station = this._api.frameData.space_stations.find(
          s => s.uuid == this._api.frameData.ship.docked_at_station
        )
        ctx.beginPath()
        ctx.font = `bold ${sizing.dockedAtFontSize * 0.8}px courier new`
        ctx.fillStyle = '#00ff00'
        ctx.textAlign = 'center'
        ctx.fillText(
          "Docked at",
          camera.canvasHalfWidth,
          sizing.docketAtYTopOffset
        )
        ctx.font = `bold ${sizing.dockedAtFontSize}px courier new`
        ctx.fillText(
          station.name,
          camera.canvasHalfWidth,
          sizing.docketAtYTopOffset + sizing.dockedAtYInterval
        )
      }
    }
    else if (this._api.frameData.ship.parked_at_ore_mine) {
      const oreMine = this._api.frameData.ore_mines.find(
        om => om.uuid == this._api.frameData.ship.parked_at_ore_mine
      )
      if(sizing.abbreviateDockedAt) {
        ctx.beginPath()
        ctx.font = `bold ${sizing.dockedAtFontSize}px courier new`
        ctx.fillStyle = '#00ff00'
        ctx.textAlign = 'center'
        ctx.fillText(
          "Parked🪨",
          camera.canvasHalfWidth,
          sizing.docketAtYTopOffset
        )
      }else {
        ctx.beginPath()
        ctx.font = `bold ${sizing.dockedAtFontSize * 0.8}px courier new`
        ctx.fillStyle = '#00ff00'
        ctx.textAlign = 'center'
        ctx.fillText(
          "Parked at",
          camera.canvasHalfWidth,
          sizing.docketAtYTopOffset
        )
        ctx.font = `bold ${sizing.dockedAtFontSize}px courier new`
        ctx.fillText(
          oreMine.name,
          camera.canvasHalfWidth,
          sizing.docketAtYTopOffset + sizing.dockedAtYInterval
        )
      }
    }
  }

  public drawShipGravityBrakeEffectElements(
    ctx: CanvasRenderingContext2D,
    camera: Camera,
    elements: GravityBrakeShipEffectElement[],
  ) {
    if(!elements.length) {
      return
    }
    const now = performance.now()
    const cameraPosition = camera.getPosition()
    const zoom = camera.getZoom()
    for(let i in elements) {
      let el = elements[i]
      let cc = camera.mapCoordToCanvasCoord(el.mapCoord, cameraPosition)
      let percentComplete = (now - el.createdAt) / GRAVITY_BREAK_SHIP_EFFECT_ELEMENT_TTL_MS
      let alpha = 0.7 * (1 - percentComplete)
      let radiusPx = (0.75 * el.percentDeployed + percentComplete * 2) * this._api.frameData.map_config.units_per_meter / zoom
      ctx.beginPath()
      ctx.fillStyle = `rgb(0, 0, 255, ${alpha})`
      ctx.arc(cc.x, cc.y, radiusPx, 0, TWO_PI)
      ctx.fill()
    }
  }

  private drawAflameEffect(
    ctx: CanvasRenderingContext2D,
    camera: Camera,
    canvasCoord: PointCoord,
    fireBallRadiusCanvasPx: number,
  ) {
    // Draw dancing fireballs
    for(let i=0; i<3; i++) {
      let tFlameRadius = fireBallRadiusCanvasPx + randomInt(
        fireBallRadiusCanvasPx / 4,
        fireBallRadiusCanvasPx * 4,
      )
      const quarterFlameRadius = Math.max(1, Math.round(tFlameRadius / 4))
      ctx.beginPath()
      ctx.fillStyle = `rgb(255, 0, 0, 0.${randomInt(2, 5)})`
      ctx.arc(
        canvasCoord.x + randomInt(-1 * quarterFlameRadius, quarterFlameRadius),
        canvasCoord.y + randomInt(-1 * quarterFlameRadius, quarterFlameRadius),
        tFlameRadius,
        0,
        TWO_PI,
      )
      ctx.fill()
    }
    // Draw flame sparks
    const sparkLineCount = randomInt(-8, 2)
    ctx.lineWidth = Math.max(1, Math.floor(3 / camera.getZoom()))
    for(let i=0; i<sparkLineCount; i++) {
      let lineLength = fireBallRadiusCanvasPx * randomInt(9, 12)
      let angle = randomInt(0, 359)
      let linep1 = camera.getCanvasPointAtLocation(
        canvasCoord,
        angle,
        randomInt(0, Math.max(1, Math.floor(fireBallRadiusCanvasPx / 3))),
      )
      let linep2 = camera.getCanvasPointAtLocation(
        canvasCoord,
        angle,
        lineLength,
      )
      ctx.beginPath()
      ctx.strokeStyle = `rgb(255, 255, 0, 0.8)`
      ctx.moveTo(linep1.x, linep1.y)
      ctx.lineTo(linep2.x, linep2.y)
      ctx.stroke()
    }
  }

  public drawEMPBlasts(ctx: CanvasRenderingContext2D, camera: Camera) {
    for(let i in this._api.frameData.emp_blasts) {
      this.drawEMPBlast(
        ctx,
        camera,
        this._api.frameData.emp_blasts[i]
      )
    }
  }

  private drawEMPBlast(ctx: CanvasRenderingContext2D, camera: Camera, empBlast: EMPBlast){
    const ppm = this._api.frameData.map_config.units_per_meter
    const zoom = camera.getZoom()
    const cameraPosition = camera.getPosition()
    let radiusMeters: number, radiusPx: number
    const canvasCoord = camera.mapCoordToCanvasCoord(
      {x:empBlast.origin_point[0], y:empBlast.origin_point[1]},
      cameraPosition,
    )
    if(empBlast.elapsed_ms < empBlast.flare_ms) {
      const percentCompleteTime = empBlast.elapsed_ms / empBlast.flare_ms
      const percentCompleteFlareRadius = nthRoot(percentCompleteTime, 2) // x=y^2
      radiusMeters = Math.max(1, percentCompleteFlareRadius * empBlast.max_radius_meters)
      radiusPx = radiusMeters * ppm / zoom
      const maxRadiusPx = empBlast.max_radius_meters * ppm / zoom
      const gradient = ctx.createRadialGradient(
        canvasCoord.x, canvasCoord.y, 0,
        canvasCoord.x, canvasCoord.y, radiusPx,
      )
      gradient.addColorStop(0, `rgb(0, 0, 255, ${getRandomFloat(0.5, 0.8)})`)
      gradient.addColorStop(1, "rgb(0, 0, 255, 0)");
      ctx.fillStyle = gradient
      for(let i=0; i<3; i++) {
        ctx.beginPath()
        ctx.arc(
          canvasCoord.x + getRandomFloat(-1.5, 1.5) * ppm / zoom,
          canvasCoord.y + getRandomFloat(-1.5, 1.5) * ppm / zoom,
          radiusPx * getRandomFloat(0.75, 1.25),
          0,
          TWO_PI,
        )
        ctx.fill()
      }
      const dotCt = 8
      const dotRadiusPx = Math.max(1, 1.25 * ppm / zoom)
      for(let i=0; i<dotCt; i++) {
        ctx.beginPath()
        ctx.fillStyle = 'rgb(0, 0, 255)'
        ctx.arc(
          canvasCoord.x + getRandomFloat(-1 * maxRadiusPx,  maxRadiusPx),
          canvasCoord.y + getRandomFloat(-1 * maxRadiusPx, maxRadiusPx),
          dotRadiusPx,
          0,
          TWO_PI,
        )
        ctx.fill()
      }
    }
    else if(empBlast.elapsed_ms < (empBlast.flare_ms + empBlast.fade_ms)) {
      // Fadeout emp blast
      const elapsedFade = empBlast.elapsed_ms - empBlast.flare_ms
      const fadePercent = elapsedFade / empBlast.fade_ms
      const startRadius = empBlast.max_radius_meters
      const endRadius = empBlast.max_radius_meters * 1.4
      radiusMeters = startRadius + (endRadius - startRadius) * fadePercent
      const fadeRadiusPx = radiusMeters * ppm / zoom
      const alpha = 0.8 - (0.8 * fadePercent)
      const gradient = ctx.createRadialGradient(
        canvasCoord.x, canvasCoord.y, 0,
        canvasCoord.x, canvasCoord.y, fadeRadiusPx,
      )
      gradient.addColorStop(0, `rgb(0, 0, 255, ${alpha})`)
      gradient.addColorStop(1, `rgb(0, 0, 255, 0)`);
      ctx.beginPath()
      ctx.fillStyle = gradient
      ctx.arc(
        canvasCoord.x,
        canvasCoord.y,
        Math.round(fadeRadiusPx),
        0,
        TWO_PI,
      )
      ctx.fill()
      const dotCt = Math.ceil((1 - fadePercent) * 8)
      const dotRadiusPx = Math.max(1, 1 * ppm / zoom)
      for(let i=0; i<dotCt; i++) {
        ctx.beginPath()
        ctx.fillStyle = 'rgb(0, 0, 255, 0.75)'
        ctx.arc(
          canvasCoord.x + getRandomFloat(-2 * fadeRadiusPx,  fadeRadiusPx*2),
          canvasCoord.y + getRandomFloat(-2 * fadeRadiusPx, fadeRadiusPx*2),
          dotRadiusPx,
          0,
          TWO_PI,
        )
        ctx.fill()
      }
    }
  }

  public drawExplosions(ctx: CanvasRenderingContext2D, camera: Camera) {
    for(let i in this._api.frameData.explosions) {
      this.drawExplosion(
        ctx,
        camera,
        this._api.frameData.explosions[i],
      )
    }
  }

  private drawExplosion(ctx: CanvasRenderingContext2D, camera: Camera, ex: Explosion) {
    const ppm = this._api.frameData.map_config.units_per_meter
    const zoom = camera.getZoom()
    const cameraPosition = camera.getPosition()
    let radiusMeters: number, radiusPx: number
    const canvasCoord = camera.mapCoordToCanvasCoord(
      {x:ex.origin_point[0], y:ex.origin_point[1]},
      cameraPosition,
    )
    const maxFireBallRadiusCanvasPx = ex.max_radius_meters * ppm / zoom
    if(ex.elapsed_ms < ex.flame_ms) {
      const percentCompleteTime = ex.elapsed_ms / ex.flame_ms
      const percentCompleteFlameRadius = nthRoot(percentCompleteTime, 2) // x=y^2
      radiusMeters = Math.max(1, percentCompleteFlameRadius * ex.max_radius_meters + randomInt(-2, 2))
      radiusPx = radiusMeters * ppm / zoom

      // Primary fireball
      ctx.beginPath()
      ctx.fillStyle = `rgb(255, 0, 0, 0.${randomInt(4, 8)})`
      ctx.arc(
        canvasCoord.x + randomInt(-3, 3),
        canvasCoord.y + randomInt(-3, 3),
        radiusPx,
        0,
        TWO_PI,
      )
      ctx.fill()
      // Inner sub fireballs and sparks
      if(percentCompleteTime < 0.4) {
        // Inner fireballs
        const subFireBallsCount = randomInt(2, 4)
        for(let i=0; i<subFireBallsCount; i++) {
          let subFBSizePx = Math.floor(radiusMeters / getRandomFloat(2, 4)) * ppm / zoom
          ctx.beginPath()
          ctx.fillStyle = `rgb(255, ${randomInt(50, 200)}, 0, 0.${randomInt(3, 6)})`
          ctx.arc(
            canvasCoord.x + randomInt(-4, 4),
            canvasCoord.y + randomInt(-4, 4),
            subFBSizePx,
            0,
            TWO_PI,
          )
          ctx.fill()
        }
        // sparks
        const sparksPercComplete = percentCompleteTime / 0.4
        const dotCt = Math.ceil((1 - sparksPercComplete) * 12)
        const dotRadiusPx = Math.max(1, 1 * ppm / zoom)
        const exMaxRadiusMeters = ex.max_radius_meters * getRandomFloat(1, 1.2) * ppm / zoom
        const maxAlpha = 1 - sparksPercComplete
        for(let i=0; i<dotCt; i++) {
          ctx.beginPath()
          ctx.fillStyle = `rgb(255, 255, ${Math.max(0.25, maxAlpha)})`
          ctx.arc(
            canvasCoord.x + getRandomFloat(-1 * exMaxRadiusMeters, exMaxRadiusMeters),
            canvasCoord.y + getRandomFloat(-1 * exMaxRadiusMeters, exMaxRadiusMeters),
            dotRadiusPx,
            0,
            TWO_PI,
          )
          ctx.fill()
        }
      }
      // Debris lines
      const debrisLineCount = randomInt(-6, 6)
      ctx.beginPath()
      ctx.lineWidth = 2
      for(let i=0; i<debrisLineCount; i++) {
        let lineLength = maxFireBallRadiusCanvasPx * randomInt(1, 6)
        let angle = randomInt(0, 359)
        let linep1 = camera.getCanvasPointAtLocation(
          canvasCoord,
          angle,
          randomInt(0, Math.max(1, Math.floor(maxFireBallRadiusCanvasPx / 10))),
        )
        let linep2 = camera.getCanvasPointAtLocation(
          canvasCoord,
          angle,
          lineLength,
        )
        ctx.beginPath()
        ctx.strokeStyle = `rgb(255, 220, 220, 0.${randomInt(2, 9)})`
        ctx.moveTo(linep1.x, linep1.y)
        ctx.lineTo(linep2.x, linep2.y)
        ctx.stroke()
      }
      // White flash
      const whiteFlashTTLMS = Math.min(500, ex.flame_ms / 2)
      if(ex.elapsed_ms < whiteFlashTTLMS) {
        const whiteFlashRadiusPx = ex.max_radius_meters * 45 * ppm / zoom
        const whiteFlashPercentComplete = ex.elapsed_ms / whiteFlashTTLMS
        const gradient = ctx.createRadialGradient(
          canvasCoord.x, canvasCoord.y, 0,
          canvasCoord.x, canvasCoord.y, whiteFlashRadiusPx,
        )
        gradient.addColorStop(0, `rgb(255, 255, 255, ${1 - whiteFlashPercentComplete})`)
        gradient.addColorStop(1, "rgb(255, 255, 255, 0)");
        ctx.fillStyle = gradient
        ctx.arc(canvasCoord.x, canvasCoord.y, whiteFlashRadiusPx, 0,  TWO_PI)
        ctx.fill()
      }
    }
    else if(ex.elapsed_ms < (ex.flame_ms + ex.fade_ms)) {
      // Fadeout smoke puff
      const elapsedFade = ex.elapsed_ms - ex.flame_ms
      const fadePercent = elapsedFade / ex.fade_ms
      const startRadius = ex.max_radius_meters
      const endRadius = ex.max_radius_meters * 1.4
      radiusMeters = startRadius + (endRadius - startRadius) * fadePercent
      const fadeRadiusPx = radiusMeters * ppm / zoom
      const alpha = 0.4 - (0.4 * fadePercent)
      ctx.beginPath()
      ctx.fillStyle = `rgb(255, 0, 0, ${alpha})`
      ctx.arc(
        canvasCoord.x,
        canvasCoord.y,
        Math.round(fadeRadiusPx),
        0,
        TWO_PI,
      )
      ctx.fill()
    }
  }

  public drawExplosionShockwaves(ctx: CanvasRenderingContext2D, camera: Camera,) {
    if (!this._api.frameData.explosion_shockwaves.length) {
      return
    }
    this._api.frameData.explosion_shockwaves.forEach(esw => {
      this.drawExplosionShockwave(ctx, camera, esw)
    })
  }

  public drawExplosionShockwave(
    ctx: CanvasRenderingContext2D,
    camera: Camera,
    esw: {id: string, origin_point: Array<number>, radius_meters: number}
  ) {

    const _explosion_shockwave_max_radius_meters = 4000
    const fillAlpha = 0.12 * (1 - esw.radius_meters / _explosion_shockwave_max_radius_meters)
    const startFadeOutAtMeters = _explosion_shockwave_max_radius_meters * 0.92;
    let alphaMultiplier = 1
    if(esw.radius_meters > startFadeOutAtMeters) {
      alphaMultiplier = 1 - ((esw.radius_meters - startFadeOutAtMeters) / (_explosion_shockwave_max_radius_meters - startFadeOutAtMeters))
    }

    // Primary arc
    ctx.beginPath()
    ctx.strokeStyle = `rgb(127, 127, 127, ${getRandomFloat(0.3, 0.7) * alphaMultiplier})`
    ctx.fillStyle = `rgb(255, 255, 255, ${fillAlpha})`
    ctx.lineWidth = Math.max(
      2,
      Math.ceil(10 * this._api.frameData.map_config.units_per_meter / camera.getZoom()),
    )
    const swCenterCanvasCoord = camera.mapCoordToCanvasCoord(
      {x: esw.origin_point[0], y: esw.origin_point[1]},
      camera.getPosition()
    )
    const radiusCanvasPx = esw.radius_meters * this._api.frameData.map_config.units_per_meter / camera.getZoom()
    ctx.arc(swCenterCanvasCoord.x, swCenterCanvasCoord.y, radiusCanvasPx, 0, TWO_PI)
    ctx.stroke()
    ctx.fill()

    // Suplementary arcs
    ctx.beginPath()
    ctx.strokeStyle = `rgb(127, 127, 127, ${getRandomFloat(0.3, 0.7) * alphaMultiplier})`
    const radiusCanvasPx1 = Math.max(1, radiusCanvasPx + randomInt(
      -30 * this._api.frameData.map_config.units_per_meter / camera.getZoom(),
      30 * this._api.frameData.map_config.units_per_meter / camera.getZoom(),
    ))
    ctx.arc(swCenterCanvasCoord.x, swCenterCanvasCoord.y, radiusCanvasPx1, 0, TWO_PI)
    ctx.stroke()
    ctx.beginPath()
    ctx.strokeStyle = `rgb(127, 127, 127, ${getRandomFloat(0.3, 0.7) * alphaMultiplier})`
    const radiusCanvasPx2 = Math.max(1, radiusCanvasPx + randomInt(
      -30 * this._api.frameData.map_config.units_per_meter / camera.getZoom(),
      30 * this._api.frameData.map_config.units_per_meter / camera.getZoom(),
    ))
    ctx.arc(swCenterCanvasCoord.x, swCenterCanvasCoord.y, radiusCanvasPx2, 0, TWO_PI)
    ctx.stroke()
  }

  private drawRotatedImg(
    ctx: CanvasRenderingContext2D,
    img: HTMLImageElement,
    angleDegrees: number,
    x: number,
    y: number,
    w: number,
    h: number,
  ) : void {
    // Thanks https://stackoverflow.com/a/43927355
    ctx.save()
    ctx.translate(x+w/2, y+h/2);
    ctx.rotate(angleDegrees * PI_OVER_180);
    ctx.translate(-x-w/2, -y-h/2);
    ctx.drawImage(img, x, y, w, h);
    ctx.restore()
  }


  private drawLockVisualIndicator(
    ctx: CanvasRenderingContext2D,
    alpha: number,
    target: DrawableShip,
  ) {
    let lineWidth = 3
    const useYellow = this._api.frameData.ship.scanner_mode == "ir"
    if(this._api.frameData.ship.scanner_locking) {
      // If locking: blink crosshair, slow at first, faster as lock is obtained
      const timer = this._api.frameData.ship.timers.find(t => t.slug === TIMER_SLUG_SCANNER_LOCKING)
      if(!timer) {
        return console.warn("expected to find timer")
      }
      let skipCheck = false
      if(this.onForCount && this.onForCount < this.minOnCount) {
        this.onForCount++
        skipCheck = true
      } else if(this.onForCount && this.onForCount >= this.minOnCount) {
        this.onForCount = 0
        this.lockingCounter = 0
      }
      if(!skipCheck) {
        this.lockingCounter++
        const percent = timer.percent / 100
        const modDenominator = Math.max(1, Math.floor(this.maxLockingModLength * (1 - percent)))
        const mod = this.lockingCounter % modDenominator
        if (mod){
          return
        }
        this.onForCount = 1
      }
    } else {
      // If locked, no blinking, and
      lineWidth = 5
    }

    const midX  = (target.canvasBoundingBox.x2 + target.canvasBoundingBox.x1) / 2
    const midY  = (target.canvasBoundingBox.y2 + target.canvasBoundingBox.y1) / 2
    const dx = target.canvasBoundingBox.x2 - target.canvasBoundingBox.x1
    const dy = target.canvasBoundingBox.y2 - target.canvasBoundingBox.y1
    const maxRadius = Math.max(dx, dy)
    const distance = maxRadius * this._api.frameData.ship.scanner_lock_traversal_slack
    // Vertical CrossHairs
    ctx.beginPath()
    ctx.strokeStyle = `rgb(255, ${useYellow?'255':'0'}, 0, ${alpha / 2})`
    ctx.lineWidth = lineWidth
    ctx.beginPath()
    ctx.moveTo(midX + distance, midY + maxRadius)
    ctx.lineTo(midX + distance, midY - maxRadius)
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(midX - distance, midY + maxRadius)
    ctx.lineTo(midX - distance, midY - maxRadius)
    ctx.stroke()
    // Horizontal Crosshairs
    ctx.beginPath()
    ctx.moveTo(midX - maxRadius, midY + distance)
    ctx.lineTo(midX + maxRadius, midY + distance)
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(midX - maxRadius, midY - distance)
    ctx.lineTo(midX + maxRadius, midY - distance)
    ctx.stroke()

    if(this._api.frameData.ship.scanner_locked && Math.random() < 0.8) {
      // Diamond Lock
      const buffer = 0//randomInt(-2, 2)
      ctx.beginPath()
      ctx.lineWidth = 2
      ctx.strokeStyle = `rgb(255, ${useYellow?'255':'0'}, 0, ${alpha})`
      ctx.moveTo(midX, midY - (maxRadius + buffer)) // top mid
      ctx.lineTo(midX + maxRadius + buffer, midY) // mid right
      ctx.lineTo(midX, midY + maxRadius + buffer) // bottom mid
      ctx.lineTo(midX - (maxRadius + buffer), midY) // mid left
      ctx.lineTo(midX, midY - (maxRadius + buffer)) // top mid
      ctx.stroke()
    }
  }

  public drawShip(
    ctx: CanvasRenderingContext2D,
    camera: Camera,
    drawableShip: DrawableShip,
    scannerTargetIDCursor: string | null,
    drawBoundingBox: boolean,
  ) {

    const currentZoom = camera.getZoom()

    if(drawableShip.exploded){
      return
    }

    if (drawableShip.isDot) {
      ctx.beginPath()
      ctx.fillStyle = "rgb(0, 255, 0, 0.9)"
      ctx.arc(
        drawableShip.canvasCoordCenter.x,
        drawableShip.canvasCoordCenter.y,
        camera.minSizeForDotPx - 1,
        0,
        TWO_PI,
      )
      ctx.fill()
    }

    // Visual Shake x/y offsets
    let vsxo = 0, vsyo = 0;
    if(
      drawableShip.isSelf
      && this._api.lastShockwaveFrame !== null
      && (this._api.lastShockwaveFrame + 75) > this._api.frameData.game_frame
    ) {
      const percentThroughShake = (this._api.frameData.game_frame - this._api.lastShockwaveFrame) / 75
      const shakeReduction = 1 - percentThroughShake
      const xOffsetM = getRandomFloat(-2 * shakeReduction, 2 * shakeReduction)
      const yOffsetM = getRandomFloat(-2 * shakeReduction, 2 * shakeReduction)
      vsxo = xOffsetM * this._api.frameData.map_config.units_per_meter / currentZoom
      vsyo = yOffsetM * this._api.frameData.map_config.units_per_meter / currentZoom
    }
    const shipLenXPX = SHIP_LENGTH_METERS_X * this._api.frameData.map_config.units_per_meter / currentZoom
    const shipLenYPX = SHIP_LENGTH_METERS_Y * this._api.frameData.map_config.units_per_meter / currentZoom
    const shipX1 = (drawableShip.canvasCoordCenter.x + vsxo) - (shipLenXPX / 2)
    const shipY1 = (drawableShip.canvasCoordCenter.y + vsyo) - (shipLenYPX / 2)

    const img = this._asset.shipAssetRegister[drawableShip.skinSlug] || this._asset.backupShipAsset
    this.drawRotatedImg(
      ctx,
      img,
      drawableShip.heading,
      shipX1,
      shipY1,
      shipLenXPX,
      shipLenYPX,
    )

    if(drawableShip.miningOreLocation) {
      let mupm = this._api.frameData.map_config.units_per_meter
      const om = this._api.frameData.ore_mines.find(o => o.uuid == drawableShip.miningOreLocation)
      if(om) {
        const p1 = camera.mapCoordToCanvasCoord(
          {x: om.position_map_units_x, y: om.position_map_units_y},
          camera.getPosition(),
        )
        const rockRadiusCanvasPx = om.collision_radius_meters * this._api.frameData.map_config.units_per_meter / currentZoom
        p1.x += getRandomFloat(rockRadiusCanvasPx * -1, rockRadiusCanvasPx)
        p1.y += getRandomFloat(rockRadiusCanvasPx * -1, rockRadiusCanvasPx)
        ctx.beginPath()
        ctx.strokeStyle = "rgb(255, 0, 0, 0.6)"
        ctx.lineWidth = 4
        ctx.moveTo(drawableShip.HBNoseCanvasCoord.x, drawableShip.HBNoseCanvasCoord.y)
        ctx.lineTo(p1.x, p1.y)
        ctx.stroke()
        ctx.beginPath()
        ctx.fillStyle = `rgb(255, 0, 0, ${getRandomFloat(0.2, 0.5)})`
        ctx.arc(
          p1.x, p1.y, getRandomFloat(2, 6) * mupm / currentZoom, 0, TWO_PI
        )
        ctx.fill()
        if(Math.random() >= 0.85) {
          this._camera.addFlameSmokeElement(
            {
              x: om.position_map_units_x + getRandomFloat(-1*om.collision_radius_meters*mupm, om.collision_radius_meters*mupm),
              y: om.position_map_units_y + getRandomFloat(-1*om.collision_radius_meters*mupm, om.collision_radius_meters*mupm),
            },
            getRandomFloat(2, 5)
          )
        }
      }
    }

    if(drawableShip.aflame) {
      const flameRadiusCanvasPx = Math.max(1, SHIP_LENGTH_METERS_Y * this._api.frameData.map_config.units_per_meter / currentZoom / 5)
      this.drawAflameEffect(
        ctx,
        camera,
        drawableShip.canvasCoordCenter,
        flameRadiusCanvasPx,
      )
    }

    if(drawBoundingBox && drawableShip.canvasBoundingBox && !drawableShip.exploded) {
      const shipIsLockedOrLocking = drawableShip.shipId === this._api.frameData.ship.scanner_lock_target && (
        this._api.frameData.ship.scanner_locked || this._api.frameData.ship.scanner_locking
      )
      const cursorOnShip = drawableShip.shipId === scannerTargetIDCursor
      // We dont want to draw bounding box if diamond lock box will be drawn
      if(!shipIsLockedOrLocking || (shipIsLockedOrLocking && !this._api.frameData.ship.scanner_locked)) {
        ctx.beginPath()
        ctx.strokeStyle = drawableShip.isSelf ? "rgb(200, 200, 200, 0.40)" : "rgb(255, 0, 0, 0.85)"
        ctx.lineWidth = 2.5
        ctx.rect(
          drawableShip.canvasBoundingBox.x1,
          drawableShip.canvasBoundingBox.y1,
          drawableShip.canvasBoundingBox.x2 - drawableShip.canvasBoundingBox.x1,
          drawableShip.canvasBoundingBox.y2 - drawableShip.canvasBoundingBox.y1,
        )
        ctx.stroke()
      }

      const bbXOffset = drawableShip.canvasBoundingBox.x1
      let bbYOffset = drawableShip.canvasBoundingBox.y2 + 20
      const bbYInterval = 20
      ctx.beginPath()
      ctx.font = 'bold 18px Courier New'
      ctx.fillStyle = drawableShip.isSelf ? "rgb(200, 200, 200, 0.85)" : "rgb(255, 0, 0, 0.85)"
      ctx.textAlign = 'left'
      let desigPrefix = cursorOnShip ? "👉" : ""
      if(!drawableShip.alive) {
        desigPrefix = desigPrefix + "💀"
      }
      ctx.fillText(desigPrefix + drawableShip.designator, bbXOffset, bbYOffset)
      bbYOffset += bbYInterval
      if(drawableShip.distance) {
        ctx.fillText(`${drawableShip.distance} M`, bbXOffset, bbYOffset)
        bbYOffset += bbYInterval
      }
      if (shipIsLockedOrLocking && this._api.frameData.ship.scanner_lock_traversal_slack !== null) {
        this.drawLockVisualIndicator(
          ctx,
          getRandomFloat(0.62, 0.95),
          drawableShip,
        )
      }
    }
    const tubeFireAnimationFrameCt = 15
    if(
      drawableShip.lastTubeFireFrame !== null
      && (drawableShip.lastTubeFireFrame + tubeFireAnimationFrameCt) >= this._api.frameData.game_frame
    ) {
      const percentComplete = (this._api.frameData.game_frame - drawableShip.lastTubeFireFrame) / tubeFireAnimationFrameCt
      const radiusPx = (this._api.frameData.map_config.units_per_meter / currentZoom) * ((percentComplete * 10) + 4)
      ctx.beginPath()
      ctx.fillStyle = `rgb(200, 200, 200, ${1 - percentComplete})`
      ctx.arc(
        drawableShip.HBNoseCanvasCoord.x,
        drawableShip.HBNoseCanvasCoord.y,
        radiusPx, 0, TWO_PI
      )
      ctx.fill()
    }

    if(drawableShip.visualEbeamChargePercent > 0) {
      const maxSizeRadius = 3.5 * getRandomFloat(0.9, 1.25) * this._api.frameData.map_config.units_per_meter / currentZoom
      const radiusPx = maxSizeRadius * drawableShip.visualEbeamChargePercent
      ctx.beginPath()
      ctx.fillStyle = Math.random() > 0.5 ?`rgb(255, 255, 0, ${getRandomFloat(0.3, 0.8)})`: `rgb(255, 0, 0, ${getRandomFloat(0.3, 0.8)})`
      ctx.arc(
        drawableShip.HBBottomRightCanvasCoord.x + vsxo + (getRandomFloat(-1, 1) * this._api.frameData.map_config.units_per_meter / currentZoom),
        drawableShip.HBBottomRightCanvasCoord.y + vsyo + (getRandomFloat(-1, 1) * this._api.frameData.map_config.units_per_meter / currentZoom),
        radiusPx, 0, TWO_PI
      )
      ctx.fill()
      ctx.beginPath()
      ctx.arc(
        drawableShip.HBBottomLeftCanvasCoord.x + vsxo + (getRandomFloat(-1, 1) * this._api.frameData.map_config.units_per_meter / currentZoom),
        drawableShip.HBBottomLeftCanvasCoord.y + vsyo + (getRandomFloat(-1, 1) * this._api.frameData.map_config.units_per_meter / currentZoom),
        radiusPx, 0, TWO_PI
      )
      ctx.fill()
    }
    if(drawableShip.visualEbeamFiring) {
      ctx.beginPath()
      ctx.strokeStyle = `rgb(255, 0, 0, ${getRandomFloat(0.5, 0.9)})`
      ctx.lineWidth = getRandomFloat(0.85, 1.15) * this._api.frameData.map_config.units_per_meter / currentZoom
      ctx.moveTo(drawableShip.HBBottomRightCanvasCoord.x, drawableShip.HBBottomRightCanvasCoord.y)
      ctx.lineTo(drawableShip.HBNoseCanvasCoord.x, drawableShip.HBNoseCanvasCoord.y)
      ctx.lineTo(drawableShip.HBBottomLeftCanvasCoord.x, drawableShip.HBBottomLeftCanvasCoord.y)
      ctx.stroke()
      ctx.beginPath()
      ctx.fillStyle = `rgb(255, 0, 0, ${getRandomFloat(0.45, 0.8)})`
      ctx.arc(
        drawableShip.HBNoseCanvasCoord.x, drawableShip.HBNoseCanvasCoord.y,
        getRandomFloat(1.5, 2) * this._api.frameData.map_config.units_per_meter / currentZoom,
        0, TWO_PI
      )
      ctx.fill()

      const lineCt = randomInt(3, 6)
      for(let i=0; i<lineCt; i++) {
        let lineLengthPx = getRandomFloat(5, 12) * this._api.frameData.map_config.units_per_meter / currentZoom
        let angle = randomInt(0, 359)
        let lineP2 = camera.getCanvasPointAtLocation(
          drawableShip.HBNoseCanvasCoord,
          angle,
          lineLengthPx,
        )
        ctx.beginPath()
        ctx.strokeStyle = `rgb(255, 220, 220, 0.${randomInt(6, 9)})`
        ctx.lineWidth = 0.4 * this._api.frameData.map_config.units_per_meter / currentZoom
        ctx.moveTo(drawableShip.HBNoseCanvasCoord.x, drawableShip.HBNoseCanvasCoord.y)
        ctx.lineTo(lineP2.x, lineP2.y)
        ctx.stroke()
      }
    }

    if(drawableShip.engineLit) {
      // Primary engine Flame
      let radiusPx = 1.75 * this._api.frameData.map_config.units_per_meter / currentZoom
      ctx.beginPath()
      ctx.fillStyle = "#ff0000"
      ctx.arc(
        drawableShip.EngineOuterLeftCanvasCoord.x + vsxo,
        drawableShip.EngineOuterLeftCanvasCoord.y + vsyo,
        radiusPx * getRandomFloat(0.9, 1.1),
        0, TWO_PI,
      )
      ctx.fill()
      ctx.beginPath()
      ctx.arc(
        drawableShip.EngineInnerLeftCanvasCoord.x + vsxo,
        drawableShip.EngineInnerLeftCanvasCoord.y + vsyo,
        radiusPx * getRandomFloat(0.9, 1.1),
        0, TWO_PI,
      )
      ctx.fill()
      ctx.beginPath()
      ctx.arc(
        drawableShip.EngineOuterRightCanvasCoord.x + vsxo,
        drawableShip.EngineOuterRightCanvasCoord.y + vsyo,
        radiusPx * getRandomFloat(0.9, 1.1),
        0, TWO_PI,
      )
      ctx.fill()
      ctx.beginPath()
      ctx.arc(
        drawableShip.EngineInnerRightCanvasCoord.x + vsxo,
        drawableShip.EngineInnerRightCanvasCoord.y + vsyo,
        radiusPx * getRandomFloat(0.9, 1.1),
        0, TWO_PI,
      )
      ctx.fill()
      // inner engine Flame
      radiusPx = 0.7 * this._api.frameData.map_config.units_per_meter / currentZoom
      let maxInnerShake = radiusPx * 0.35
      ctx.beginPath()
      ctx.fillStyle = `rgb(255, 160, 0, ${getRandomFloat(0.2, 0.5)})`
      ctx.arc(
        drawableShip.EngineOuterLeftCanvasCoord.x + vsxo + getRandomFloat(-maxInnerShake, maxInnerShake),
        drawableShip.EngineOuterLeftCanvasCoord.y + vsyo + getRandomFloat(-maxInnerShake, maxInnerShake),
        radiusPx * getRandomFloat(0.5, 1.25),
        0, TWO_PI,
      )
      ctx.fill()
      ctx.beginPath()
      ctx.fillStyle = `rgb(255, 160, 0, ${getRandomFloat(0.2, 0.5)})`
      ctx.arc(
        drawableShip.EngineInnerLeftCanvasCoord.x + vsxo + getRandomFloat(-maxInnerShake, maxInnerShake),
        drawableShip.EngineInnerLeftCanvasCoord.y + vsyo + getRandomFloat(-maxInnerShake, maxInnerShake),
        radiusPx * getRandomFloat(0.5, 1.25),
        0, TWO_PI,
      )
      ctx.fill()
      ctx.beginPath()
      ctx.fillStyle = `rgb(255, 160, 0, ${getRandomFloat(0.2, 0.5)})`
      ctx.arc(
        drawableShip.EngineOuterRightCanvasCoord.x + vsxo + getRandomFloat(-maxInnerShake, maxInnerShake),
        drawableShip.EngineOuterRightCanvasCoord.y + vsyo + getRandomFloat(-maxInnerShake, maxInnerShake),
        radiusPx * getRandomFloat(0.5, 1.25),
        0, TWO_PI,
      )
      ctx.fill()
      ctx.beginPath()
      ctx.fillStyle = `rgb(255, 160, 0, ${getRandomFloat(0.2, 0.5)})`
      ctx.arc(
        drawableShip.EngineInnerRightCanvasCoord.x + vsxo + getRandomFloat(-maxInnerShake, maxInnerShake),
        drawableShip.EngineInnerRightCanvasCoord.y + vsyo + getRandomFloat(-maxInnerShake, maxInnerShake),
        radiusPx * getRandomFloat(0.5, 1.25),
        0, TWO_PI,
      )
      ctx.fill()
    }

    if(drawableShip.visualScannerMode !== null) {
      const color = drawableShip.visualScannerMode=="ir"?a=>`rgb(255, 255, 0, ${a})`:a=>`rgb(0, 255, 0, ${a})`
      const radiusPx = drawableShip.visualScannerRangeMeters * this._api.frameData.map_config.units_per_meter / currentZoom
      const interval = 2500 / ((drawableShip.visualScannerSensitivity || 0) + 1)
      const ratationPercentStart = ((performance.now() + this.getNameHash(drawableShip.designator)) % interval) / interval
      const ratationPercentEnd = ratationPercentStart + 0.02
      const gradient = ctx.createRadialGradient(
        drawableShip.canvasCoordCenter.x, drawableShip.canvasCoordCenter.y, 0,
        drawableShip.canvasCoordCenter.x, drawableShip.canvasCoordCenter.y, radiusPx,
      )
      gradient.addColorStop(0, color(0.12))
      gradient.addColorStop(1, color(0.02));
      ctx.beginPath()
      ctx.fillStyle = gradient
      ctx.moveTo(drawableShip.canvasCoordCenter.x, drawableShip.canvasCoordCenter.y)
      ctx.arc(
        drawableShip.canvasCoordCenter.x, drawableShip.canvasCoordCenter.y,
        radiusPx,
        TWO_PI*ratationPercentStart,
        TWO_PI*ratationPercentEnd,
      )
      ctx.lineTo(drawableShip.canvasCoordCenter.x, drawableShip.canvasCoordCenter.y)
      ctx.fill()
    }

    if (this.isDebug) {
      // Draw hitbox polygon
      ctx.beginPath()
      ctx.strokeStyle = "#ff0000"
      ctx.lineWidth = 1
      ctx.moveTo(drawableShip.HBNoseCanvasCoord.x, drawableShip.HBNoseCanvasCoord.y)
      ctx.lineTo(drawableShip.HBBottomRightCanvasCoord.x, drawableShip.HBBottomRightCanvasCoord.y)
      ctx.lineTo(drawableShip.HBBottomCenterCanvasCoord.x, drawableShip.HBBottomCenterCanvasCoord.y)
      ctx.lineTo(drawableShip.HBBottomLeftCanvasCoord.x, drawableShip.HBBottomLeftCanvasCoord.y)
      ctx.lineTo(drawableShip.HBNoseCanvasCoord.x, drawableShip.HBNoseCanvasCoord.y)
      ctx.stroke()

      // Draw engine nodes
      ctx.beginPath() // OUTER LEFT RED
      ctx.fillStyle = "#ff0000"
      ctx.arc(
        drawableShip.EngineOuterLeftCanvasCoord.x,
        drawableShip.EngineOuterLeftCanvasCoord.y,
        4, 0, TWO_PI
      )
      ctx.fill()
      ctx.beginPath() // INNER LEFT GREEN
      ctx.fillStyle = "#00ff00"
      ctx.arc(
        drawableShip.EngineInnerLeftCanvasCoord.x,
        drawableShip.EngineInnerLeftCanvasCoord.y,
        4, 0, TWO_PI
      )
      ctx.fill()
      ctx.beginPath() // INNER RIGHT YELLOW
      ctx.fillStyle = "#ffff00"
      ctx.arc(
        drawableShip.EngineInnerRightCanvasCoord.x,
        drawableShip.EngineInnerRightCanvasCoord.y,
        4, 0, TWO_PI
      )
      ctx.fill()
      ctx.beginPath() // OUTER RIGHT BLUE
      ctx.fillStyle = "#0000ff"
      ctx.arc(
        drawableShip.EngineOuterRightCanvasCoord.x,
        drawableShip.EngineOuterRightCanvasCoord.y,
        4, 0, TWO_PI
      )
      ctx.fill()
    }
  }

  public drawHunterDrone(
    ctx: CanvasRenderingContext2D,
    camera: Camera,
    drone: DrawableHunterDrone,
  ){
    const currentZoom = camera.getZoom()
    if (drone.isDot) {
      ctx.beginPath()
      ctx.fillStyle = "rgb(0, 255, 0, 0.9)"
      ctx.arc(
        drone.canvasCoordCenter.x,
        drone.canvasCoordCenter.y,
        camera.minSizeForDotPx - 1,
        0,
        TWO_PI,
      )
      ctx.fill()
    }
    const droneLenXPX = HUNTER_DRONE_LENGTH_METERS_X * this._api.frameData.map_config.units_per_meter / currentZoom
    const droneLenYPX = HUNTER_DRONE_LENGTH_METERS_Y * this._api.frameData.map_config.units_per_meter / currentZoom
    const droneX1 = (drone.canvasCoordCenter.x) - (droneLenXPX / 2)
    const droneY1 = (drone.canvasCoordCenter.y) - (droneLenYPX / 2)
    this.drawRotatedImg(
      ctx,
      this._asset.hunterDroneAsset,
      drone.visualHeading,
      droneX1,
      droneY1,
      droneLenXPX,
      droneLenYPX,
    )
    // Engine flame
    if(drone.percentArmed > 0.9) {
      let radiusPx = 1.25 * this._api.frameData.map_config.units_per_meter / currentZoom
      ctx.beginPath()
      ctx.fillStyle = "#ff0000"
      ctx.arc(
        drone.HBBottomCenterCanvasCoord.x,
        drone.HBBottomCenterCanvasCoord.y,
        radiusPx * getRandomFloat(0.9, 1.1),
        0, TWO_PI,
      )
      ctx.fill()
      // inner engine Flame
      radiusPx = 0.5 * this._api.frameData.map_config.units_per_meter / currentZoom
      let maxInnerShake = radiusPx * 0.35
      ctx.beginPath()
      ctx.fillStyle = `rgb(255, 160, 0, ${getRandomFloat(0.2, 0.5)})`
      ctx.arc(
        drone.HBBottomCenterCanvasCoord.x + getRandomFloat(-maxInnerShake, maxInnerShake),
        drone.HBBottomCenterCanvasCoord.y + getRandomFloat(-maxInnerShake, maxInnerShake),
        radiusPx * getRandomFloat(0.5, 1.25),
        0, TWO_PI,
      )
      ctx.fill()
    }

    ctx.strokeStyle = drone.isFriendly? "rgb(200, 200, 200, 0.85)": "rgb(255, 0, 0, 0.85)"
    ctx.lineWidth = 1.75 + (1.5 * drone.percentArmed)
    if(drone.percentArmed > 0.97) {
      ctx.beginPath()
      ctx.rect(
        drone.canvasBoundingBox.x1,
        drone.canvasBoundingBox.y1,
        drone.canvasBoundingBox.x2 - drone.canvasBoundingBox.x1,
        drone.canvasBoundingBox.y2 - drone.canvasBoundingBox.y1,
      )
      ctx.stroke()
    } else {
      // Draw arming animation with bounding box.
      const topLen = drone.canvasBoundingBox.x2 - drone.canvasBoundingBox.x1
      const sideLen = drone.canvasBoundingBox.y2 - drone.canvasBoundingBox.y1
      // Top Line (left to right)
      if(drone.percentArmed >= 0.25) {
        ctx.beginPath()
        ctx.moveTo(drone.canvasBoundingBox.x1, drone.canvasBoundingBox.y1)
        ctx.lineTo(drone.canvasBoundingBox.x2, drone.canvasBoundingBox.y1)
        ctx.stroke()
      } else {
        let percSide = drone.percentArmed / 0.25
        ctx.beginPath()
        ctx.moveTo(drone.canvasBoundingBox.x1, drone.canvasBoundingBox.y1)
        ctx.lineTo(drone.canvasBoundingBox.x1 + (topLen * percSide), drone.canvasBoundingBox.y1)
        ctx.stroke()
      }
      // right side line (top to bottom)
      if(drone.percentArmed >= 0.50) {
        ctx.beginPath()
        ctx.moveTo(drone.canvasBoundingBox.x2, drone.canvasBoundingBox.y1)
        ctx.lineTo(drone.canvasBoundingBox.x2, drone.canvasBoundingBox.y2)
        ctx.stroke()
      } else if (drone.percentArmed >= 0.25 && drone.percentArmed < 0.5) {
        let percSide = (drone.percentArmed - 0.25) / 0.25
        ctx.beginPath()
        ctx.moveTo(drone.canvasBoundingBox.x2, drone.canvasBoundingBox.y1)
        ctx.lineTo(drone.canvasBoundingBox.x2, drone.canvasBoundingBox.y1 + (sideLen * percSide))
        ctx.stroke()
      }
      // bottom line (right to left)
      if(drone.percentArmed >= 0.75) {
        ctx.beginPath()
        ctx.moveTo(drone.canvasBoundingBox.x1, drone.canvasBoundingBox.y2)
        ctx.lineTo(drone.canvasBoundingBox.x2, drone.canvasBoundingBox.y2)
        ctx.stroke()
      } else if (drone.percentArmed >= 0.50 && drone.percentArmed < 0.75) {
        let percSide = (drone.percentArmed - 0.5) / 0.25
        ctx.beginPath()
        ctx.moveTo(drone.canvasBoundingBox.x2, drone.canvasBoundingBox.y2)
        ctx.lineTo(drone.canvasBoundingBox.x2 - (topLen * percSide), drone.canvasBoundingBox.y2)
        ctx.stroke()
      }
      // left side (bottom to top)
      if(drone.percentArmed > 0.75 && drone.percentArmed <= 0.97) {
        let percSide = (drone.percentArmed - 0.75) / 0.25
        ctx.beginPath()
        ctx.moveTo(drone.canvasBoundingBox.x1, drone.canvasBoundingBox.y2)
        ctx.lineTo(drone.canvasBoundingBox.x1, drone.canvasBoundingBox.y2 - (sideLen * percSide))
        ctx.stroke()
      }
    }
    const bbXOffset = drone.canvasBoundingBox.x1
    const bbYOffsetInterval = 20
    let bbYOffset = drone.canvasBoundingBox.y2 + bbYOffsetInterval
    ctx.beginPath()
    ctx.font = 'bold 18px Courier New'
    ctx.fillStyle = drone.isFriendly? "rgb(200, 200, 200, 0.85)": "rgb(255, 0, 0, 0.85)"
    ctx.textAlign = 'left'
    ctx.fillText("HTR.Drone", bbXOffset, bbYOffset)
    bbYOffset += bbYOffsetInterval
    ctx.fillText(`${drone.distance} M`, bbXOffset, bbYOffset)
  }

  public drawMagnetMine(
    ctx: CanvasRenderingContext2D,
    mine: DrawableMagnetMine,
  ) {
    const percentRotated = (performance.now() % 1000) / 1000
    this.drawRotatedImg(
      ctx,
      this._asset.magnetMineAsset,
      percentRotated * 360,
      mine.canvasX1, mine.canvasY1,
      mine.canvasW, mine.canvasH,
    )
    ctx.strokeStyle = "rgb(255, 0, 0, 0.85)"
    ctx.lineWidth = 1.75 + (1.5 * mine.percentArmed)
    if(mine.percentArmed > 0.97) {
      ctx.beginPath()
      ctx.rect(
        mine.canvasBoundingBox.x1,
        mine.canvasBoundingBox.y1,
        mine.canvasBoundingBox.x2 - mine.canvasBoundingBox.x1,
        mine.canvasBoundingBox.y2 - mine.canvasBoundingBox.y1,
      )
      ctx.stroke()
    } else {
      // Draw arming animation with bounding box.
      const topLen = mine.canvasBoundingBox.x2 - mine.canvasBoundingBox.x1
      const sideLen = mine.canvasBoundingBox.y2 - mine.canvasBoundingBox.y1
      // Top Line (left to right)
      if(mine.percentArmed >= 0.25) {
        ctx.beginPath()
        ctx.moveTo(mine.canvasBoundingBox.x1, mine.canvasBoundingBox.y1)
        ctx.lineTo(mine.canvasBoundingBox.x2, mine.canvasBoundingBox.y1)
        ctx.stroke()
      } else {
        let percSide = mine.percentArmed / 0.25
        ctx.beginPath()
        ctx.moveTo(mine.canvasBoundingBox.x1, mine.canvasBoundingBox.y1)
        ctx.lineTo(mine.canvasBoundingBox.x1 + (topLen * percSide), mine.canvasBoundingBox.y1)
        ctx.stroke()
      }
      // right side line (top to bottom)
      if(mine.percentArmed >= 0.50) {
        ctx.beginPath()
        ctx.moveTo(mine.canvasBoundingBox.x2, mine.canvasBoundingBox.y1)
        ctx.lineTo(mine.canvasBoundingBox.x2, mine.canvasBoundingBox.y2)
        ctx.stroke()
      } else if (mine.percentArmed >= 0.25 && mine.percentArmed < 0.5) {
        let percSide = (mine.percentArmed - 0.25) / 0.25
        ctx.beginPath()
        ctx.moveTo(mine.canvasBoundingBox.x2, mine.canvasBoundingBox.y1)
        ctx.lineTo(mine.canvasBoundingBox.x2, mine.canvasBoundingBox.y1 + (sideLen * percSide))
        ctx.stroke()
      }
      // bottom line (right to left)
      if(mine.percentArmed >= 0.75) {
        ctx.beginPath()
        ctx.moveTo(mine.canvasBoundingBox.x1, mine.canvasBoundingBox.y2)
        ctx.lineTo(mine.canvasBoundingBox.x2, mine.canvasBoundingBox.y2)
        ctx.stroke()
      } else if (mine.percentArmed >= 0.50 && mine.percentArmed < 0.75) {
        let percSide = (mine.percentArmed - 0.5) / 0.25
        ctx.beginPath()
        ctx.moveTo(mine.canvasBoundingBox.x2, mine.canvasBoundingBox.y2)
        ctx.lineTo(mine.canvasBoundingBox.x2 - (topLen * percSide), mine.canvasBoundingBox.y2)
        ctx.stroke()
      }
      // left side (bottom to top)
      if(mine.percentArmed > 0.75 && mine.percentArmed <= 0.97) {
        let percSide = (mine.percentArmed - 0.75) / 0.25
        ctx.beginPath()
        ctx.moveTo(mine.canvasBoundingBox.x1, mine.canvasBoundingBox.y2)
        ctx.lineTo(mine.canvasBoundingBox.x1, mine.canvasBoundingBox.y2 - (sideLen * percSide))
        ctx.stroke()
      }
    }
    const bbXOffset = mine.canvasBoundingBox.x1
    const bbYOffsetInterval = 20
    let bbYOffset = mine.canvasBoundingBox.y2 + bbYOffsetInterval
    ctx.beginPath()
    ctx.font = 'bold 18px Courier New'
    ctx.fillStyle = "rgb(255, 0, 0, 0.85)"
    ctx.textAlign = 'left'
    ctx.fillText("MAG.Mine", bbXOffset, bbYOffset)
    bbYOffset += bbYOffsetInterval
    ctx.fillText(`${mine.distance} M`, bbXOffset, bbYOffset)

  }

  public drawMagnetMineTargetingLines(ctx: CanvasRenderingContext2D, lines: DrawableMagnetMineTargetingLine[]) {
    for(let i in lines) {
      if(Math.random() > 0.65) {
        continue
      }
      let l = lines[i]
      ctx.beginPath()
      ctx.strokeStyle = Math.random() > 0.5 ? `rgb(0, 0, 255, ${getRandomFloat(0.1, 0.6)})` : `rgb(255, 0, 0, ${getRandomFloat(0.1, 0.6)})`
      ctx.lineWidth = 2
      ctx.moveTo(l.mineCanvasCoord.x, l.mineCanvasCoord.y)
      ctx.lineTo(l.targetCanvasCoord.x, l.targetCanvasCoord.y)
      ctx.stroke()
    }
  }

  public drawEMP(ctx: CanvasRenderingContext2D, emp: DrawableEMP) {
    ctx.beginPath()
    ctx.fillStyle = "#0000ff"
    ctx.arc(emp.canvasCoordCenter.x, emp.canvasCoordCenter.y, emp.radiusCanvasPX, 0, TWO_PI)
    ctx.fill()
    if(Math.random() < 0.5){
      ctx.beginPath()
      ctx.arc(emp.canvasCoordCenter.x, emp.canvasCoordCenter.y, emp.radiusCanvasPX * 1.5, 0, TWO_PI)
      ctx.lineWidth = emp.radiusCanvasPX
      ctx.strokeStyle = `rgb(60, 60, 255, ${getRandomFloat(0.4, 0.8)})`
      ctx.stroke()
    }
  }

  private getIconFontSize(camera: Camera) {
    const zoomIx = camera.getZoomIndex()
    if (zoomIx <= 10) {
      return 28
    } else if (zoomIx == 9) {
      return 23
    } else if (zoomIx == 8) {
      return 20
    } else {
      return 18
    }
  }

  public drawSpaceStations(ctx: CanvasRenderingContext2D, camera: Camera,) {
    const cameraPosition = camera.getPosition()
    const cameraZoom = camera.getZoom()
    for(let i in this._api.frameData.space_stations) {
      const st = this._api.frameData.space_stations[i]
      const centerCanvasCoord = camera.mapCoordToCanvasCoord(
        {x: st.position_map_units_x, y: st.position_map_units_y},
        cameraPosition,
      )

      const sideXLengthCanvasPx = Math.floor(
        (
          STATION_LENGTH_METERS_X
          * this._api.frameData.map_config.units_per_meter
        )/ cameraZoom)
      if(sideXLengthCanvasPx < 10) {
        const iconFontSize = this.getIconFontSize(camera)
        ctx.beginPath()
        ctx.font = iconFontSize + "px Courier New";
        ctx.fillStyle = "#ffffff";
        ctx.textAlign = 'center';
        ctx.textBaseline = "middle";
        ctx.fillText(
          "🛰️",
          centerCanvasCoord.x,
          centerCanvasCoord.y,
        );
      }
      else {
        // Draw
        const sideYLengthCanvasPx = Math.floor(
          (
            STATION_LENGTH_METERS_Y
            * this._api.frameData.map_config.units_per_meter
          ) / cameraZoom)
        const stationImgX1 = centerCanvasCoord.x - (sideXLengthCanvasPx/2)
        const stationImgY1 = centerCanvasCoord.y - (sideYLengthCanvasPx/2)
        ctx.drawImage(
          this._asset.stationAsset,
          stationImgX1, stationImgY1,
          sideXLengthCanvasPx, sideYLengthCanvasPx
        )
        // Draw service perimeter
        const servicePerimeterCavasPx = st.service_radius_map_units / cameraZoom
        const perimeterWidth = Math.ceil(4 * this._api.frameData.map_config.units_per_meter / cameraZoom)
        if(Math.random() > 0.8) {
          ctx.beginPath()
          ctx.strokeStyle = Math.random() > 0.5 ? "rgb(0, 0, 255, 0.3)" : "rgb(0, 0, 255, 0.7)"
          ctx.lineWidth = perimeterWidth
          ctx.arc(
            centerCanvasCoord.x, centerCanvasCoord.y,
            servicePerimeterCavasPx,
            0,
            TWO_PI,
          )
          ctx.stroke()
        }
        ctx.beginPath()
        ctx.strokeStyle = "rgb(0, 0, 255, 0.35)"
        ctx.lineWidth = 1
        ctx.arc(
          centerCanvasCoord.x, centerCanvasCoord.y,
          servicePerimeterCavasPx,
          0,
          TWO_PI,
        )
        ctx.stroke()

        // Draw spotlight effect
        const spotLightIntervalMS = 6000
        const spotLightPercent = (performance.now() % spotLightIntervalMS) / spotLightIntervalMS
        const spotLightStartAngle = TWO_PI * spotLightPercent
        const spotLightEndAngle = spotLightStartAngle + TWO_PI * 0.125
        const spotLightRadiusPx = 70 * this._api.frameData.map_config.units_per_meter / cameraZoom
        const gradient = ctx.createRadialGradient(
          centerCanvasCoord.x, centerCanvasCoord.y, 0,
          centerCanvasCoord.x, centerCanvasCoord.y, spotLightRadiusPx,
        )
        gradient.addColorStop(0, `rgb(255, 221, 148, ${getRandomFloat(0.2, 0.3)})`)
        gradient.addColorStop(1, "rgb(255, 221, 148, 0)");
        ctx.beginPath()
        ctx.fillStyle = gradient
        ctx.moveTo(centerCanvasCoord.x, centerCanvasCoord.y)
        ctx.arc(
          centerCanvasCoord.x, centerCanvasCoord.y,
          spotLightRadiusPx,
          spotLightStartAngle, spotLightEndAngle,
        )
        ctx.lineTo(centerCanvasCoord.x, centerCanvasCoord.y)
        ctx.fill()
        // Draw capture effect
        const grav_brake_last_caught: number | undefined = this._api.frameData.ship.scouted_station_gravity_brake_catches_last_frame[st.uuid]
        if(
          grav_brake_last_caught !== undefined
          && (grav_brake_last_caught + 18 > this._api.frameData.game_frame)
        ) {
          const frame = this._api.frameData.game_frame - grav_brake_last_caught + 1
          if(frame < 12 || Math.random() > 0.8) {
            ctx.beginPath()
            ctx.strokeStyle = `rgb(124, 0, 166, 0.${randomInt(20, 80)})`
            ctx.lineWidth = Math.max(1, Math.ceil(perimeterWidth * frame))
            ctx.arc(
              centerCanvasCoord.x, centerCanvasCoord.y,
              servicePerimeterCavasPx,
              0,
              TWO_PI,
            )
            ctx.stroke()
          }
        }
      }
    }
  }

  public drawMiningLocations(ctx: CanvasRenderingContext2D, camera: Camera,) {
    const cameraPosition = camera.getPosition()
    const minRockRadius = 10
    const cameraZoom = camera.getZoom()
    for(let ix in this._api.frameData.ore_mines) {
      let om = this._api.frameData.ore_mines[ix]
      let centerCanvasCoord = camera.mapCoordToCanvasCoord(
        {
          x: om.position_map_units_x,
          y: om.position_map_units_y,
        },
        cameraPosition,
      )

      let percentage: number | null = null
      const remainingOre = this._api.frameData.ship.scouted_mine_ore_remaining[om.uuid]
      if(typeof remainingOre !== "undefined") {
        percentage =  remainingOre / om.starting_ore_amount_kg
      }

      const servicePerimeterRadiusCavasPx = om.service_radius_map_units / cameraZoom
      const rockRadiusCavasPx =  om.collision_radius_meters * this._api.frameData.map_config.units_per_meter / cameraZoom
      if(rockRadiusCavasPx < minRockRadius) {
        const iconFontSize = this.getIconFontSize(camera)
        ctx.beginPath()
        ctx.font = iconFontSize + "px Courier New";
        ctx.fillStyle = "#ffffff";
        ctx.textAlign = 'center';
        ctx.textBaseline = "middle";
        ctx.fillText(
          "💎",
          centerCanvasCoord.x,
          centerCanvasCoord.y,
        );
        if(percentage !== null) {
          ctx.beginPath()
          ctx.lineWidth = 3
          ctx.strokeStyle = "#c7a600"
          ctx.arc(centerCanvasCoord.x, centerCanvasCoord.y - 5, iconFontSize * 0.7, 0, TWO_PI * percentage)
          ctx.stroke()
        }
      }
      else {
        this.drawMiningLocation(ctx, camera, om, centerCanvasCoord, rockRadiusCavasPx, servicePerimeterRadiusCavasPx, percentage)
      }
    }
  }
  private drawMiningLocation(
    ctx: CanvasRenderingContext2D,
    camera: Camera,
    om: OreMine,
    centerCanvasCoord: PointCoord,
    rockRadiusCavasPx: number,
    servicePerimeterRadiusCavasPx: number,
    minedPercentage: number | null,
  ) {
    const cameraZoom = camera.getZoom()
    const imgX1 = centerCanvasCoord.x - rockRadiusCavasPx
    const imgY1 = centerCanvasCoord.y - rockRadiusCavasPx
    const imgLen = rockRadiusCavasPx  * 2
    const rotatedPercent = (performance.now() % 27000) / 27000
    this.drawRotatedImg(
      ctx,
      this._asset.miningLocationAsset,
      360 * rotatedPercent,
      imgX1, imgY1, imgLen, imgLen
    )
    // Mined out percentage indicator
    if(minedPercentage !== null) {
      ctx.beginPath()
      ctx.strokeStyle = `rgb(255, 255, 0, 0.${randomInt(10, 30)})`
      ctx.lineWidth = (rockRadiusCavasPx / 7)
      ctx.arc(
        centerCanvasCoord.x, centerCanvasCoord.y,
        rockRadiusCavasPx + (rockRadiusCavasPx / 6),
        0, TWO_PI * minedPercentage
      )
      ctx.stroke()
    }
    // Draw lights
    console.log({minedPercentage})
    const lightColor = Boolean(minedPercentage)? a=>`rgb(255, 221, 148, ${a})`:a=>`rgb(200, 0, 0, ${a})`
    const bulbRadius = Math.floor(
      Math.max(
        1,
        2 * this._api.frameData.map_config.units_per_meter / cameraZoom,
      )
    )
    const effectRadius = Math.floor(
      Math.max(
        1,
        om.service_radius_meters * this._api.frameData.map_config.units_per_meter / cameraZoom,
      )
    )
    const gradientFillPercent = 0.8
    const gradientMin = 0.07
    const gradientMax = 0.15
    if(Math.random() < 0.97) {
      // Top Center Light
      ctx.beginPath()
      ctx.fillStyle = "rgb(255, 221, 148)"
      ctx.arc(
        centerCanvasCoord.x, centerCanvasCoord.y - servicePerimeterRadiusCavasPx,
        bulbRadius, 0, TWO_PI
      )
      ctx.fill()
      const gradient = ctx.createRadialGradient(
        centerCanvasCoord.x, centerCanvasCoord.y - servicePerimeterRadiusCavasPx, 0,
        centerCanvasCoord.x, centerCanvasCoord.y - servicePerimeterRadiusCavasPx, effectRadius,
      )
      gradient.addColorStop(0, lightColor(getRandomFloat(gradientMin, gradientMax)))
      gradient.addColorStop(gradientFillPercent, lightColor(0));
      ctx.beginPath()
      ctx.fillStyle = gradient
      ctx.moveTo(centerCanvasCoord.x, centerCanvasCoord.y - servicePerimeterRadiusCavasPx)
      ctx.arc(
        centerCanvasCoord.x, centerCanvasCoord.y - servicePerimeterRadiusCavasPx,
        effectRadius, TWO_PI*0.15, TWO_PI*0.35
      )
      ctx.lineTo(centerCanvasCoord.x, centerCanvasCoord.y - servicePerimeterRadiusCavasPx)
      ctx.fill()
    }
    if(Math.random() < 0.97) {
      // Right Hand Light
      ctx.beginPath()
      ctx.fillStyle = "rgb(255, 221, 148)"
      ctx.arc(
        centerCanvasCoord.x + servicePerimeterRadiusCavasPx, centerCanvasCoord.y,
        bulbRadius, 0, TWO_PI
      )
      ctx.fill()
      const gradient = ctx.createRadialGradient(
        centerCanvasCoord.x + servicePerimeterRadiusCavasPx, centerCanvasCoord.y, 0,
        centerCanvasCoord.x + servicePerimeterRadiusCavasPx, centerCanvasCoord.y, effectRadius,
      )
      gradient.addColorStop(0, lightColor(getRandomFloat(gradientMin, gradientMax)))
      gradient.addColorStop(gradientFillPercent, lightColor(0));
      ctx.beginPath()
      ctx.fillStyle = gradient
      ctx.moveTo(centerCanvasCoord.x +servicePerimeterRadiusCavasPx , centerCanvasCoord.y)
      ctx.arc(
        centerCanvasCoord.x + servicePerimeterRadiusCavasPx, centerCanvasCoord.y,
        effectRadius, TWO_PI*0.4, TWO_PI*0.6
      )
      ctx.lineTo(centerCanvasCoord.x +servicePerimeterRadiusCavasPx , centerCanvasCoord.y)
      ctx.fill()
    }
    if(Math.random() < 0.97) {
      // Bottom Light
      ctx.beginPath()
      ctx.fillStyle = "rgb(255, 221, 148)"
      ctx.arc(
        centerCanvasCoord.x, centerCanvasCoord.y + servicePerimeterRadiusCavasPx,
        bulbRadius, 0, TWO_PI
      )
      ctx.fill()
      const gradient = ctx.createRadialGradient(
        centerCanvasCoord.x, centerCanvasCoord.y + servicePerimeterRadiusCavasPx, 0,
        centerCanvasCoord.x, centerCanvasCoord.y + servicePerimeterRadiusCavasPx, effectRadius,
      )
      gradient.addColorStop(0, lightColor(getRandomFloat(gradientMin, gradientMax)))
      gradient.addColorStop(gradientFillPercent, lightColor(0));
      ctx.beginPath()
      ctx.fillStyle = gradient
      ctx.moveTo(centerCanvasCoord.x, centerCanvasCoord.y + servicePerimeterRadiusCavasPx)
      ctx.arc(
        centerCanvasCoord.x, centerCanvasCoord.y + servicePerimeterRadiusCavasPx,
        effectRadius, TWO_PI*0.65, TWO_PI*0.85,
      )
      ctx.lineTo(centerCanvasCoord.x, centerCanvasCoord.y + servicePerimeterRadiusCavasPx)
      ctx.fill()
    }
    if(Math.random() < 0.97) {
      // Left Hand Light
      ctx.fill()
      ctx.beginPath()
      ctx.fillStyle = "rgb(255, 221, 148)"
      ctx.arc(
        centerCanvasCoord.x - servicePerimeterRadiusCavasPx, centerCanvasCoord.y,
        bulbRadius, 0, TWO_PI
      )
      ctx.fill()
      const gradient = ctx.createRadialGradient(
        centerCanvasCoord.x - servicePerimeterRadiusCavasPx, centerCanvasCoord.y, 0,
        centerCanvasCoord.x - servicePerimeterRadiusCavasPx, centerCanvasCoord.y, effectRadius,
      )
      gradient.addColorStop(0, lightColor(getRandomFloat(gradientMin, gradientMax)))
      gradient.addColorStop(gradientFillPercent, lightColor(0));
      ctx.beginPath()
      ctx.fillStyle = gradient
      ctx.moveTo(centerCanvasCoord.x - servicePerimeterRadiusCavasPx, centerCanvasCoord.y)
      ctx.arc(
        centerCanvasCoord.x - servicePerimeterRadiusCavasPx, centerCanvasCoord.y,
        effectRadius, TWO_PI*0.9, TWO_PI*1.1
      )
      ctx.lineTo(centerCanvasCoord.x - servicePerimeterRadiusCavasPx, centerCanvasCoord.y)
      ctx.fill()
    }
  }

}
