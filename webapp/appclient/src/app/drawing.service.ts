import { Injectable } from '@angular/core';

import { ApiService } from './api.service';
import { CameraService } from './camera.service';
import { FormattingService } from './formatting.service';
import { QuoteService, QuoteDetails } from './quote.service';
import { UserService } from "./user.service";
import {
  BoxCoords
} from "./models/box-coords.model"
import {
  DrawableShip,
  VisionCircle,
  EBeamRayDetails,
} from "./models/drawable-objects.model"
import { TimerItem } from './models/timer-item.model';
import { PointCoord } from './models/point-coord.model';



const randomInt = function (min: number, max: number): number  {
  return Math.floor(Math.random() * (max - min) + min)
}


@Injectable({
  providedIn: 'root'
})
export class DrawingService {

  private deathQuote: QuoteDetails | null = null;

  private actionTileImgEngineLit: any = new Image()
  private actionTileImgEngineOnline: any = new Image()
  private actionTileImgScannerOnline: any = new Image()

  constructor(
    private _camera: CameraService,
    private _api: ApiService,
    private _formatting: FormattingService,
    private _quote: QuoteService,
    public _user: UserService,
  ) {
    this.deathQuote = this._quote.getQuote()

    this.actionTileImgEngineLit.src = "/static/img/light-engine.jpg"
    this.actionTileImgEngineOnline.src = "/static/img/activate-engine.jpg"
    this.actionTileImgScannerOnline.src = "/static/img/activate-scanner.jpg"
  }


  public drawMapBoundary(
    ctx: CanvasRenderingContext2D,
    mapWallCanvasBoxCoords: BoxCoords,
  ) {
    ctx.beginPath()
    ctx.strokeStyle ="#636300"
    ctx.lineWidth = Math.max(1, 500 / this._camera.getZoom())
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
      ctx.beginPath()
      ctx.fillStyle = vs.color
      ctx.arc(
        vs.canvasCoord.x,
        vs.canvasCoord.y,
        vs.radius,
        0,
        2 * Math.PI,
      )
      ctx.fill()
    }
  }

  public drawEbeams(
    ctx: CanvasRenderingContext2D,
    rays: EBeamRayDetails[],
  ) {
    const ebeamThickness = this._camera.getEBeamLineThickness()
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

  public drawBottomRightOverlay(
    ctx: CanvasRenderingContext2D,
  ) {
    const brcYInterval = 45
    let brcYOffset = 30
    const brcXOffset = 15
    const timerBarLength = Math.round(this._camera.canvasWidth / 8)
    const textRAlignXOffset = brcXOffset + timerBarLength + 10
    const barRAlignXOffset = brcXOffset + timerBarLength

    // Game Time
    ctx.strokeStyle = '#ffffff'
    ctx.fillStyle = '#ffffff'
    ctx.lineWidth = 1
    ctx.textAlign = 'right'
    ctx.font = 'bold 24px Courier New'
    ctx.beginPath()
    ctx.fillText(
      this._api.frameData.elapsed_time,
      this._camera.canvasWidth - 15,
      this._camera.canvasHeight - brcYOffset,
    )

    // Timers
    if(this._api.frameData.ship.alive){
      ctx.font = '20px Courier New'
      ctx.strokeStyle = '#00ff00'
      ctx.fillStyle = '#00ff00'
      brcYOffset += brcYInterval
      for(let i in this._api.frameData.ship.timers) {
        const timer: TimerItem = this._api.frameData.ship.timers[i]
        const fillLength = Math.round((timer.percent / 100) * timerBarLength)
        ctx.beginPath()
        ctx.fillText(
          timer.name,
          this._camera.canvasWidth - textRAlignXOffset,
          this._camera.canvasHeight - brcYOffset,
        )
        ctx.beginPath()
        ctx.rect(
          this._camera.canvasWidth - barRAlignXOffset, //    top left x
          this._camera.canvasHeight - (brcYOffset + 20),  // top left y
          timerBarLength, // width
          30,             // height
        )
        ctx.stroke()
        ctx.beginPath()
        ctx.rect(
          this._camera.canvasWidth - barRAlignXOffset, //    top left x
          this._camera.canvasHeight - (brcYOffset + 20),  // top left y
          fillLength, // width
          30,         // height
        )
        ctx.fill()
        brcYOffset += brcYInterval
      }
    }
  }

  public drawTopRightOverlay(
    ctx: CanvasRenderingContext2D,
  ) {
    // Gyroscope circle
    const buffer = 3;
    const gryroscopeRadius = Math.floor(this._camera.canvasHalfHeight / 8)
    const gryroscopeX = this._camera.canvasWidth - (gryroscopeRadius + buffer)
    const gryroscopeY = gryroscopeRadius + buffer
    ctx.beginPath()
    ctx.fillStyle = "rgb(255, 255, 255, 0.65)"
    ctx.arc(
      gryroscopeX,
      gryroscopeY,
      gryroscopeRadius,
      0,
      2 * Math.PI,
    )
    ctx.fill()

    // Gyroscope relative velocity indicator line
    if(
      this._api.frameData.ship.velocity_x_meters_per_second
      || this._api.frameData.ship.velocity_y_meters_per_second
    ) {
      const angleRads = this._camera.getCanvasAngleBetween(
        {x:0, y:0},
        {
          x: gryroscopeX + this._api.frameData.ship.velocity_x_meters_per_second * 1000,
          y: gryroscopeY + this._api.frameData.ship.velocity_y_meters_per_second * 1000,
        }
      ) * (Math.PI / 180)
      const gyroLinePointB = {
        x: gryroscopeX + Math.round(gryroscopeRadius * Math.sin(angleRads)),
        y: gryroscopeY + Math.round(gryroscopeRadius * Math.cos(angleRads)),
      }
      ctx.beginPath()
      ctx.strokeStyle = '#000000'
      ctx.lineWidth = 4
      ctx.moveTo(gryroscopeX, gryroscopeY)
      ctx.lineTo(gyroLinePointB.x, gyroLinePointB.y)
      ctx.stroke()
    }

    // Scanner Traversal Crosshairs
    if(this._api.frameData.ship.scanner_lock_traversal_slack !== null) {
      const crossOffset = gryroscopeRadius * this._api.frameData.ship.scanner_lock_traversal_slack
      ctx.beginPath()
      ctx.strokeStyle = 'rgb(255, 0, 0, 0.75)'
      ctx.lineWidth = 4
      // Verticle hairs
      ctx.moveTo(gryroscopeX - crossOffset, gryroscopeY - gryroscopeRadius)
      ctx.lineTo(gryroscopeX - crossOffset, gryroscopeY + gryroscopeRadius)
      ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(gryroscopeX + crossOffset, gryroscopeY - gryroscopeRadius)
      ctx.lineTo(gryroscopeX + crossOffset, gryroscopeY + gryroscopeRadius)
      ctx.stroke()

      // Horizontal hairs
      ctx.beginPath()
      ctx.moveTo(gryroscopeX - gryroscopeRadius, gryroscopeY - crossOffset)
      ctx.lineTo(gryroscopeX + gryroscopeRadius, gryroscopeY - crossOffset)
      ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(gryroscopeX - gryroscopeRadius, gryroscopeY + crossOffset)
      ctx.lineTo(gryroscopeX + gryroscopeRadius, gryroscopeY + crossOffset)
      ctx.stroke()
    }

    // Velocity Text
    const velocity = Math.sqrt(
      Math.pow(this._api.frameData.ship.velocity_x_meters_per_second, 2)
      + Math.pow(this._api.frameData.ship.velocity_y_meters_per_second, 2)
    ).toFixed(1)
    ctx.beginPath()
    ctx.font = 'bold 22px Courier New'
    ctx.fillStyle = 'rgb(255, 181, 43,  0.95)'
    ctx.textAlign = 'right'
    ctx.fillText(
      velocity + " M/S",
      this._camera.canvasWidth - 3,
      gryroscopeY + gryroscopeRadius + 18,
    )
    // Thermal Signature Text
    ctx.beginPath()
    ctx.fillText(
      this._api.frameData.ship.scanner_thermal_signature + " IR ",
      this._camera.canvasWidth - 3,
      gryroscopeY + gryroscopeRadius + 40,
    )
  }

  public drawTopLeftOverlay(ctx: CanvasRenderingContext2D) {
    const tlcYInterval = 34
    const tlcKFYInterval = 28
    let tlcYOffset = 25
    const tlcXOffset = 15
    if(this._api.frameData.ship.alive){
      // Fuel amount
      ctx.beginPath()
      ctx.font = '24px Courier New'
      ctx.fillStyle = '#fcb8b8'
      ctx.textAlign = 'left'
      ctx.fillText("⛽ " + this._formatting.formatNumber(this._api.frameData.ship.fuel_level), tlcXOffset, tlcYOffset)
      tlcYOffset += tlcYInterval

      // Battery amount
      ctx.beginPath()
      ctx.fillStyle = '#fcf9b8'
      ctx.fillText("🔋 " + this._formatting.formatNumber(this._api.frameData.ship.battery_power), tlcXOffset, tlcYOffset)
      tlcYOffset += tlcYInterval

      // Camera mode
      ctx.beginPath()
      ctx.fillStyle = '#ffffff'
      ctx.fillText("🎥 " + this._camera.getMode().toUpperCase(), tlcXOffset, tlcYOffset)
      tlcYOffset += tlcYInterval
    }
    // Killfeed (TOP LEFT)
    tlcYOffset += tlcYInterval
    ctx.font = '20px Courier New'
    ctx.fillStyle = '#ffffff'
    ctx.textAlign = 'left'
    for(let i in this._api.frameData.killfeed) {
      const kfe = this._api.frameData.killfeed[i]
      ctx.beginPath()
      ctx.fillText("💀 " + kfe.victim_name, tlcXOffset, tlcYOffset)
      tlcYOffset += tlcKFYInterval
    }
  }

  public drawBottomLeftOverlay(ctx: CanvasRenderingContext2D) {
    let lrcYOffset = this._camera.canvasHeight - 30
    let lrcYInterval = 40
    const lrcXOffset = 15
    // Scale Bar
    const barLengthMeters = (
      (
        (this._camera.canvasWidth / 4)
        * this._camera.getZoom()
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
    ctx.lineTo((this._camera.canvasWidth / 4) + lrcXOffset, lrcYOffset);
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(lrcXOffset, lrcYOffset);
    ctx.lineTo( lrcXOffset, lrcYOffset - 10);
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo((this._camera.canvasWidth / 4) + lrcXOffset, lrcYOffset);
    ctx.lineTo((this._camera.canvasWidth / 4) + lrcXOffset, lrcYOffset - 10);
    ctx.stroke()
    // Scale meters and user handle
    ctx.beginPath()
    ctx.font = '24px serif'
    ctx.fillStyle = this._api.frameData.ship.alive ? '#ffffff' : "#ff0000";
    ctx.textAlign = 'left'
    ctx.fillText(scaleLabel, lrcXOffset + 8, lrcYOffset - 12)
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
      if(this._api.frameData.ship.fuel_level < 1200) {
        ctx.beginPath()
        ctx.fillText("⚠️ LOW FUEL", lrcXOffset, lrcYOffset)
        lrcYOffset -= lrcYInterval
      }
      if(this._api.frameData.ship.battery_power < 45000) {
        ctx.beginPath()
        ctx.fillText("⚠️ LOW POWER", lrcXOffset, lrcYOffset)
        lrcYOffset -= lrcYInterval
      }
      if (this._api.frameData.ship.engine_lit) {
        ctx.drawImage(
          this.actionTileImgEngineLit,
          lrcXOffset,
          lrcYOffset - 100,
          100, 100,
        )
        lrcYOffset -= 120
      }
      else if (this._api.frameData.ship.engine_online) {
        ctx.drawImage(
          this.actionTileImgEngineOnline,
          lrcXOffset,
          lrcYOffset - 100,
          100, 100,
        )
        lrcYOffset -= 120
      }
      if(this._api.frameData.ship.scanner_online) {
        ctx.drawImage(
          this.actionTileImgScannerOnline,
          lrcXOffset,
          lrcYOffset - 100,
          100, 100,
        )
        lrcYOffset -= 120
      }
    }
  }

  public drawFrontAndCenterAlerts(ctx: CanvasRenderingContext2D) {
    if (this._api.frameData.winning_team == this._api.frameData.ship.team_id) {
      ctx.beginPath()
      ctx.font = 'bold 65px courier new'
      ctx.fillStyle = '#ffffff'
      ctx.textAlign = 'center'
      ctx.fillText("SUCCESS 🏆🚀", this._camera.canvasHalfWidth, this._camera.canvasHalfHeight / 2)
    }
    else if(!this._api.frameData.ship.alive) {
      ctx.beginPath()
      ctx.font = 'bold 56px courier new'
      ctx.fillStyle = '#ff0000'
      ctx.textAlign = 'center'
      let deathTextYOffset = this._camera.canvasHalfHeight / 3
      const deathQuoteOffset = 50
      if(this._api.frameData.game_frame % 50 > 25) {
        ctx.fillText("GAME OVER", this._camera.canvasHalfWidth, deathTextYOffset)
      }
      deathTextYOffset += (deathQuoteOffset * 2)
      ctx.beginPath()
      ctx.fillStyle = '#9e9e9e'
      ctx.textAlign = 'left'
      ctx.font = 'bold 40px Verdana'
      for(let i in this.deathQuote.lines) {
        const prefix = parseInt(i) === 0 ? '"' : ""
        ctx.fillText(prefix + this.deathQuote.lines[i], 100, deathTextYOffset)
        deathTextYOffset += deathQuoteOffset
      }
      ctx.font = 'bold 32px Verdana'
      deathTextYOffset += deathQuoteOffset * 0.5
      ctx.beginPath()
      ctx.fillText("- " + (this.deathQuote.author || "Unknown"), 100, deathTextYOffset)
    }
  }

  private drawAflameEffect(
    ctx: CanvasRenderingContext2D,
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
        2 * Math.PI,
      )
      ctx.fill()
    }
    // Draw flame sparks
    const sparkLineCount = randomInt(-8, 2)
    ctx.lineWidth = Math.max(1, Math.floor(3 / this._camera.getZoom()))
    for(let i=0; i<sparkLineCount; i++) {
      let lineLength = fireBallRadiusCanvasPx * randomInt(9, 12)
      let angle = randomInt(0, 359)
      let linep1 = this._camera.getCanvasPointAtLocation(
        canvasCoord,
        angle,
        randomInt(0, Math.max(1, Math.floor(fireBallRadiusCanvasPx / 3))),
      )
      let linep2 = this._camera.getCanvasPointAtLocation(
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

  private drawExplosionFrameEffect(
    ctx: CanvasRenderingContext2D,
    canvasCoord: PointCoord,
    explosionFrame: number,
    maxFireBallRadiusCanvasPx: number,
  ) {
    if(explosionFrame < 8) {
      let fbSize = (explosionFrame / 7) * maxFireBallRadiusCanvasPx
      ctx.beginPath()
      ctx.fillStyle = 'rgb(255, 0, 0, 1)'
      ctx.arc(
        canvasCoord.x + randomInt(-3, 3),
        canvasCoord.y + randomInt(-3, 3),
        fbSize,
        0,
        2 * Math.PI,
      )
      ctx.fill()
    } else if (explosionFrame < 76) {
      // Main fireball
      let fbSize = maxFireBallRadiusCanvasPx * (randomInt(5, 8) / 7)
      ctx.beginPath()
      ctx.fillStyle = `rgb(255, 0, 0, 0.${randomInt(5, 9)})`
      ctx.arc(
        canvasCoord.x + randomInt(-3, 3),
        canvasCoord.y + randomInt(-3, 3),
        fbSize,
        0,
        2 * Math.PI,
      )
      ctx.fill()
      // Inner sub fireballs
      const subFireBallsCount = randomInt(2, 4)
      for(let i=0; i<subFireBallsCount; i++) {
        let subFBSize = Math.floor(fbSize / randomInt(2, 4))
        ctx.beginPath()
        ctx.fillStyle = `rgb(255, ${randomInt(20, 65)}, 0, 0.${randomInt(7, 9)})`
        ctx.arc(
          canvasCoord.x + randomInt(-8, 8),
          canvasCoord.y + randomInt(-8, 8),
          subFBSize,
          0,
          2 * Math.PI,
        )
        ctx.fill()
      }
      // Deris Lines
      const debrisLineCount = randomInt(-6, 6)
      ctx.lineWidth = 2
      for(let i=0; i<debrisLineCount; i++) {
        let lineLength = maxFireBallRadiusCanvasPx * randomInt(1, 6)
        let angle = randomInt(0, 359)
        let linep1 = this._camera.getCanvasPointAtLocation(
          canvasCoord,
          angle,
          randomInt(0, Math.max(1, Math.floor(maxFireBallRadiusCanvasPx / 10))),
        )
        let linep2 = this._camera.getCanvasPointAtLocation(
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
    } else {
      let smokePuffSize = maxFireBallRadiusCanvasPx * 0.9 + (explosionFrame * 1.5);
      let alpha = (1 - ((explosionFrame - 76) / 75)) / 3.75
      ctx.beginPath()
      ctx.fillStyle = `rgb(255, 0, 0, ${alpha})`
      ctx.arc(
        canvasCoord.x,
        canvasCoord.y,
        Math.round(smokePuffSize),
        0,
        2 * Math.PI,
      )
      ctx.fill()
    }
  }

  public drawShip(
    ctx: CanvasRenderingContext2D,
    drawableShip: DrawableShip,
    scannerTargetIDCursor: string | null,
  ) {

    if (drawableShip.isDot) {
      ctx.beginPath()
      ctx.fillStyle = "rgb(0, 255, 0, 0.9)"
      ctx.arc(
        drawableShip.canvasCoordCenter.x,
        drawableShip.canvasCoordCenter.y,
        this._camera.minSizeForDotPx - 1,
        0,
        2 * Math.PI,
      )
      ctx.fill()
    }

    if(drawableShip.isVisual && !drawableShip.explosionFrame) {
      // Ship is within visual range
      ctx.beginPath()
      ctx.fillStyle = drawableShip.fillColor
      ctx.moveTo(drawableShip.canvasCoordP0.x, drawableShip.canvasCoordP0.y)
      ctx.lineTo(drawableShip.canvasCoordP1.x, drawableShip.canvasCoordP1.y)
      ctx.lineTo(drawableShip.canvasCoordP2.x, drawableShip.canvasCoordP2.y)
      ctx.lineTo(drawableShip.canvasCoordP3.x, drawableShip.canvasCoordP3.y)
      ctx.closePath()
      ctx.fill()


      // fin 0
      ctx.beginPath()
      ctx.moveTo(drawableShip.canvasCoordP0.x, drawableShip.canvasCoordP0.y)
      ctx.lineTo(drawableShip.canvasCoordFin0P0.x, drawableShip.canvasCoordFin0P0.y)
      ctx.lineTo(drawableShip.canvasCoordFin0P1.x, drawableShip.canvasCoordFin0P1.y)
      ctx.closePath()
      ctx.fill()
      // fin 1
      ctx.beginPath()
      ctx.moveTo(drawableShip.canvasCoordP3.x, drawableShip.canvasCoordP3.y)
      ctx.lineTo(drawableShip.canvasCoordFin1P0.x, drawableShip.canvasCoordFin1P0.y)
      ctx.lineTo(drawableShip.canvasCoordFin1P1.x, drawableShip.canvasCoordFin1P1.y)
      ctx.closePath()
      ctx.fill()

      if(drawableShip.engineLit) {
        const engineFlameX = Math.round((drawableShip.canvasCoordP3.x + drawableShip.canvasCoordP0.x) / 2)
        const engineFlameY = Math.round((drawableShip.canvasCoordP3.y + drawableShip.canvasCoordP0.y) / 2)
        let engineOuterFlameRadius = Math.max(2, Math.round(
          Math.sqrt(
            (Math.pow(drawableShip.canvasCoordP3.x - drawableShip.canvasCoordP0.x, 2)
            + Math.pow(drawableShip.canvasCoordP3.y - drawableShip.canvasCoordP0.y, 2))
          ) / 2
        ) * (drawableShip.engineBoosted ? 4 : 1))
        engineOuterFlameRadius += randomInt(engineOuterFlameRadius / 4, engineOuterFlameRadius)
        ctx.beginPath()
        ctx.fillStyle = drawableShip.engineBoosted ? "rgb(71, 139, 255)" : "rgb(255, 0, 0, 0.9)"
        ctx.arc(
          engineFlameX,
          engineFlameY,
          engineOuterFlameRadius,
          0,
          2 * Math.PI,
        )
        ctx.fill()
        ctx.beginPath()
        ctx.fillStyle = "rgb(255, 186, 89, 0.8)"
        const engineInnerFlameRadius = Math.floor(engineOuterFlameRadius / 2) + randomInt(
          engineOuterFlameRadius / -5, engineOuterFlameRadius / 5
        )
        ctx.arc(
          engineFlameX + randomInt(engineInnerFlameRadius / -4, engineInnerFlameRadius / 4),
          engineFlameY + randomInt(engineInnerFlameRadius / -4, engineInnerFlameRadius / 4),
          engineInnerFlameRadius,
          0,
          2 * Math.PI,
        )
        ctx.fill()
      }
    }

    if(drawableShip.aflame) {
      const flameRadiusCanvasPx = Math.max(1, Math.round(
        Math.sqrt(
          (Math.pow(drawableShip.canvasCoordP1.x - drawableShip.canvasCoordP0.x, 2)
          + Math.pow(drawableShip.canvasCoordP1.y - drawableShip.canvasCoordP0.y, 2))
        ) / 4
      ))
      this.drawAflameEffect(
        ctx,
        drawableShip.canvasCoordCenter,
        flameRadiusCanvasPx,
      )
    }
    if(drawableShip.explosionFrame && drawableShip.explosionFrame < 150) {
      /* Explosion schedule
        frame 1-6 fireball growth
        frame 7-75 pulsating fireball
        frame 76-150 fading smoke puff
      */
      let maxFireBallRadius = Math.round(
        Math.sqrt(
          (Math.pow(drawableShip.canvasCoordP1.x - drawableShip.canvasCoordP0.x, 2)
          + Math.pow(drawableShip.canvasCoordP1.y - drawableShip.canvasCoordP0.y, 2))
        ) * 10
      )
      this.drawExplosionFrameEffect(
        ctx,
        drawableShip.canvasCoordCenter,
        drawableShip.explosionFrame,
        maxFireBallRadius,
      )
    }

    if(drawableShip.canvasBoundingBox && !drawableShip.explosionFrame) {
      const shipIsLocked = this._api.frameData.ship.scanner_locked && drawableShip.shipId === this._api.frameData.ship.scanner_lock_target
      const shipIsLockedOrLocking = drawableShip.shipId === this._api.frameData.ship.scanner_lock_target && (
        this._api.frameData.ship.scanner_locked || this._api.frameData.ship.scanner_locking
      )
      const cursorOnShip = drawableShip.shipId === scannerTargetIDCursor
      ctx.beginPath()
      ctx.strokeStyle = drawableShip.isSelf ? "rgb(200, 200, 200, 0.85)" : "rgb(255, 0, 0, 0.85)"
      ctx.lineWidth = 2.5
      ctx.rect(
        drawableShip.canvasBoundingBox.x1,
        drawableShip.canvasBoundingBox.y1,
        drawableShip.canvasBoundingBox.x2 - drawableShip.canvasBoundingBox.x1,
        drawableShip.canvasBoundingBox.y2 - drawableShip.canvasBoundingBox.y1,
      )
      ctx.stroke()

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
        ctx.beginPath()
        ctx.fillText(drawableShip.distance + " M", bbXOffset, bbYOffset)
        bbYOffset += bbYInterval
      }
      if(drawableShip.thermalSignature) {
        ctx.beginPath()
        ctx.fillText(
          drawableShip.thermalSignature + ` / ${this._api.frameData.ship.scanner_ir_minimum_thermal_signature} IR`,
          bbXOffset,
          bbYOffset,
        )
        bbYOffset += bbYInterval
      }
      if (shipIsLockedOrLocking && this._api.frameData.ship.scanner_lock_traversal_slack !== null) {
        const midX  = (drawableShip.canvasBoundingBox.x2 + drawableShip.canvasBoundingBox.x1) / 2
        const midY  = (drawableShip.canvasBoundingBox.y2 + drawableShip.canvasBoundingBox.y1) / 2
        const dx = drawableShip.canvasBoundingBox.x2 - drawableShip.canvasBoundingBox.x1
        const dy = drawableShip.canvasBoundingBox.y2 - drawableShip.canvasBoundingBox.y1
        const maxRadius = Math.max(dx, dy)
        const distance = maxRadius * this._api.frameData.ship.scanner_lock_traversal_slack
        // Vertical CH
        ctx.beginPath()
        ctx.strokeStyle = this._api.frameData.ship.scanner_locked ? "rgb(255, 0, 0, 0.85)" : "rgb(255, 0, 0, 0.5)"
        ctx.moveTo(midX + distance, midY + maxRadius)
        ctx.lineTo(midX + distance, midY - maxRadius)
        ctx.stroke()
        ctx.beginPath()
        ctx.moveTo(midX - distance, midY + maxRadius)
        ctx.lineTo(midX - distance, midY - maxRadius)
        ctx.stroke()
        // Horizontal CH
        ctx.beginPath()
        ctx.moveTo(midX - maxRadius, midY + distance)
        ctx.lineTo(midX + maxRadius, midY + distance)
        ctx.stroke()
        ctx.beginPath()
        ctx.moveTo(midX - maxRadius, midY - distance)
        ctx.lineTo(midX + maxRadius, midY - distance)
        ctx.stroke()
      }
    }
  }

}
