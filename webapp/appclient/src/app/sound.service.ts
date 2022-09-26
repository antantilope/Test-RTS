import { Injectable } from '@angular/core';
import { ApiService } from './api.service';
import { PointCoord } from './models/point-coord.model';


const randomInt = function (min: number, max: number): number  {
  return Math.floor(Math.random() * (max - min) + min)
}

@Injectable({
  providedIn: 'root'
})
export class SoundService {

  // Music Engine Properties
  private musicEngineInterval = 1000 / 5

  // Ambient Music
  private ambientMusicChoices = [
    "ambient-music-1.mp3",
    "ambient-music-2.mp3",
    "ambient-music-4.mp3",
    "ambient-music-5.mp3",
    "ambient-music-6.mp3",
    "ambient-music-7.mp3",
    "ambient-music-8.mp3",
  ];
  private currentTrackIx: number;

  // Death music
  private deathMusicPlaying = false
  private deathMusicChoices = [
    "death-music-1.mp3",
    "death-music-2.mp3",
    "death-music-3.mp3",
    "death-music-4.mp3",
    "death-music-5.mp3",
  ]
  private deathMusicSound: HTMLAudioElement

  // Sound Effects Engine Properties

  // Auto Pilot
  private copilotAutopilotActiveSound: HTMLAudioElement
  private copilotAutopilotOfflineSound: HTMLAudioElement
  private autoPilotActiveLastFrame = false;

  // Engine
  private copilotEngineActiveSound: HTMLAudioElement
  private copilotEngineOfflineSound: HTMLAudioElement
  private engineActiveLastFrame = false;
  private engineFiringSound: HTMLAudioElement
  private engineFiringLastFrame = false;

  // gravity break
  private copilotBrakeDeployedSound: HTMLAudioElement
  private copilotBrakeRetractedSound: HTMLAudioElement
  private brakeDeployedLastFrame = false

  // Scanner
  private enemySpottedSound: HTMLAudioElement
  private spottedEnemiesCount: number

  private copilotRadarOnlineSound: HTMLAudioElement
  private copilotIROnlineSound: HTMLAudioElement
  private copilotScannerOfflineSound: HTMLAudioElement
  private scannerOnlineLastFrame = false
  private scannerPreviousMode: string | null = null

  private copilotTargetLockedSound: HTMLAudioElement
  private targetLockedLastFrame = false
  private copilotTargeDestroyedSound: HTMLAudioElement
  private seenTargetDestroyedFrames: Array<number> = []

  private scannerLockLostSound: HTMLAudioElement

  // Ebeam
  private eBeamSound: HTMLAudioElement
  private eBeamFiringLastFrame = false
  private copilotEbeamChargingSound: HTMLAudioElement
  private ebeamChargingLastFrame = false
  private copilotEbeamReadySound: HTMLAudioElement
  private ebeamReadyLastFrame = false

  private playedSelfExplosionSound = false
  private explosionSound: HTMLAudioElement
  private fastenSeatbeltSound: HTMLAudioElement
  private shipRattlingSound: HTMLAudioElement

  private heardExplosionShockwaveIds: Array<string> = []
  private heardFastenSeatbeltShockwaveIds: Array<string> = []

  // Mining Laser
  private copilotMiningBeamActiveSound: HTMLAudioElement
  private copilotMiningBeamOfflineSound: HTMLAudioElement
  private miningBeamActiveLastFrame = false

  private copilotDeathSound: HTMLAudioElement
  private copilotDeathChoices = [
    "copilot-death-1.mp3",
    "copilot-death-2.mp3",
    "copilot-death-3.mp3",
    "copilot-death-4.mp3",
    "copilot-death-5.mp3",
  ]
  private copilotDeathSoundPlaying = false


  constructor(
    private _api: ApiService
  ) {
    console.log("SoundService::constructor()")

    // Setup music engine
    const deathMusicFile = this.deathMusicChoices[randomInt(0, this.deathMusicChoices.length)]
    this.deathMusicSound = new Audio("/static/sound/" + deathMusicFile)
    setTimeout(this.runMusicEngine.bind(this), this.musicEngineInterval)

    // Setup sound effects engine
    const copilotDeathFile = this.copilotDeathChoices[randomInt(0, this.copilotDeathChoices.length)]
    this.copilotDeathSound = new Audio("/static/sound/" + copilotDeathFile)

    // Autopilot
    this.copilotAutopilotActiveSound = new Audio("/static/sound/copilot-autopilot-active.mp3")
    this.copilotAutopilotOfflineSound = new Audio("/static/sound/copilot-autopilot-offline.mp3")

    // Engine
    this.copilotEngineActiveSound = new Audio("/static/sound/copilot-engine-active.mp3")
    this.copilotEngineOfflineSound = new Audio("/static/sound/copilot-engine-offline.mp3")
    this.engineFiringSound = new Audio("/static/sound/engine-firing.mp3")
    this.engineFiringSound.loop = true;

    // Gravity Brake
    this.copilotBrakeDeployedSound = new Audio("/static/sound/copilot-brake-deployed.mp3")
    this.copilotBrakeRetractedSound = new Audio("/static/sound/copilot-brake-retracted.mp3")

    // Scanner
    this.enemySpottedSound = new Audio("/static/sound/alert-ship-spotted.mp3")
    this.spottedEnemiesCount = 0
    this.copilotRadarOnlineSound = new Audio("/static/sound/copilot-radar-imaging-active.mp3")
    this.copilotIROnlineSound = new Audio("/static/sound/copilot-thermal-imaging-active.mp3")
    this.copilotScannerOfflineSound = new Audio("/static/sound/copilot-scanner-offline.mp3")
    this.copilotTargetLockedSound = new Audio("/static/sound/copilot-target-locked.mp3")
    this.copilotTargeDestroyedSound = new Audio("/static/sound/copilot-target-destroyed.mp3")
    this.scannerLockLostSound = new Audio("/static/sound/scanner-lock-loss.mp3")

    // Ebeam
    this.eBeamSound = new Audio("/static/sound/ebeam.mp3");
    this.copilotEbeamChargingSound = new Audio("/static/sound/copilot-weapon-charging.mp3")
    this.copilotEbeamReadySound = new Audio("/static/sound/copilot-weapon-ready.mp3")

    this.explosionSound = new Audio("/static/sound/explosion.mp3")
    this.fastenSeatbeltSound = new Audio("/static/sound/fasten-seatbelt-chime.mp3")
    this.shipRattlingSound = new Audio("/static/sound/ship-rattle.mp3")

    // Mining laser
    this.copilotMiningBeamActiveSound = new Audio("/static/sound/copilot-mining-beam-active.mp3")
    this.copilotMiningBeamOfflineSound = new Audio("/static/sound/copilot-mining-beam-offline.mp3")
  }

  public getDistanceBetweenCoords(
    p1: PointCoord,
    p2: PointCoord
  ): number {
    return Math.sqrt(
      Math.pow(p1.x - p2.x, 2)
      + Math.pow(p1.y - p2.y, 2)
    )
  }

  public runSoundFXEngine() {
    const ship = this._api.frameData.ship;

    // Copilot Autopilot alerts
    if(ship.alive && !this.autoPilotActiveLastFrame && ship.autopilot_program){
      this.autoPilotActiveLastFrame = true;
      this.copilotAutopilotActiveSound.play();
    } else if(ship.alive && this.autoPilotActiveLastFrame && !ship.autopilot_program) {
      this.autoPilotActiveLastFrame = false;
      this.copilotAutopilotOfflineSound.play();
    }

    // Engine
    if(ship.alive && !this.engineActiveLastFrame && ship.engine_online) {
      this.engineActiveLastFrame = true
      this.copilotEngineActiveSound.play()
    } else if (ship.alive && this.engineActiveLastFrame && !ship.engine_online) {
      this.engineActiveLastFrame = false
      this.copilotEngineOfflineSound.play()
    }
    // TODO: there is a large gap in sound when looping :(
    if(!this.engineFiringLastFrame && ship.engine_lit) {
      this.engineFiringLastFrame = true
      // this.engineFiringSound.play()
    } else if (this.engineFiringLastFrame && !ship.engine_lit) {
      // this.engineFiringSound.pause()
    }

    // Copilot gravity break alerts
    if(ship.alive && !this.brakeDeployedLastFrame && ship.gravity_brake_deployed) {
      this.brakeDeployedLastFrame = true
      this.copilotBrakeDeployedSound.play()
    } else if(ship.alive && this.brakeDeployedLastFrame && !ship.gravity_brake_deployed) {
      this.brakeDeployedLastFrame = false;
      this.copilotBrakeRetractedSound.play()
    }

    // Ebeam sound
    if(ship.alive && !this.eBeamFiringLastFrame && ship.ebeam_firing) {
      this.eBeamFiringLastFrame = true;
      this.eBeamSound.play();
    } else if(this.eBeamFiringLastFrame && !ship.ebeam_firing) {
      this.eBeamFiringLastFrame = false;
    }
    // Copilot ebeam alerts
    if(ship.alive && !this.ebeamChargingLastFrame && ship.ebeam_charging){
      this.ebeamChargingLastFrame = true;
      this.copilotEbeamChargingSound.play();
    } else if(this.ebeamChargingLastFrame && !ship.ebeam_charging) {
      this.ebeamChargingLastFrame = false;
    }
    if(ship.alive && !this.ebeamReadyLastFrame && ship.ebeam_can_fire){
      this.ebeamReadyLastFrame = true;
      this.copilotEbeamReadySound.play();
    } else if(this.ebeamReadyLastFrame && !ship.ebeam_can_fire) {
      this.ebeamReadyLastFrame = false;
    }

    // Mining laser
    if(ship.alive && !this.miningBeamActiveLastFrame && ship.mining_ore) {
      this.miningBeamActiveLastFrame = true
      this.copilotMiningBeamActiveSound.play()
    } else if (ship.alive && this.miningBeamActiveLastFrame && !ship.mining_ore) {
      this.miningBeamActiveLastFrame = false
      this.copilotMiningBeamOfflineSound.play()
    }

    // Ship spotted Alert
    if(ship.alive && ship.scanner_data.length > this.spottedEnemiesCount) {
      this.spottedEnemiesCount = ship.scanner_data.length;
      this.enemySpottedSound.play()
    }
    else if(ship.scanner_data.length < this.spottedEnemiesCount) {
      this.spottedEnemiesCount = ship.scanner_data.length;
    }
    // Scanner State Alerts
    if (!this.scannerOnlineLastFrame && ship.scanner_online) {
      this.scannerOnlineLastFrame = true
      if(ship.alive && ship.scanner_mode == 'radar') {
        this.scannerPreviousMode = 'radar'
        this.copilotRadarOnlineSound.play()
      } else if (ship.alive && ship.scanner_mode == 'ir') {
        this.scannerPreviousMode = 'ir'
        this.copilotIROnlineSound.play()
      }
    } else if (
      this.scannerOnlineLastFrame
      && ship.scanner_online
      && ship.scanner_mode != this.scannerPreviousMode
    ) {
      this.scannerPreviousMode = ship.scanner_mode
      if(ship.alive && ship.scanner_mode == 'radar') {
        this.copilotRadarOnlineSound.play()
      } else if (ship.alive && ship.scanner_mode == 'ir') {
        this.copilotIROnlineSound.play()
      }
    } else if(ship.alive && this.scannerOnlineLastFrame && !ship.scanner_online) {
      this.scannerOnlineLastFrame = false
      this.copilotScannerOfflineSound.play()
    }

    // Scanner Lock state
    if(ship.alive && !this.targetLockedLastFrame && ship.scanner_locked) {
      this.targetLockedLastFrame = true
      this.copilotTargetLockedSound.play()
    } else if(ship.alive && this.targetLockedLastFrame && !ship.scanner_locked) {
      this.targetLockedLastFrame = false
      this.scannerLockLostSound.play()
    }

    // Target Destoyed Copilot Alert
    if(
      ship.alive
      && ship.ebeam_last_hit_frame
      && this._api.frameData.game_frame < (ship.ebeam_last_hit_frame + 30)
      && this.seenTargetDestroyedFrames.indexOf(ship.ebeam_last_hit_frame) == -1
    ) {
      this.seenTargetDestroyedFrames.push(ship.ebeam_last_hit_frame)
      this.copilotTargeDestroyedSound.play()
    }

    if(ship.explosion_frame && !this.playedSelfExplosionSound) {
      this.playedSelfExplosionSound = true
      this.explosionSound.play()
    }
    else if(!this.playedSelfExplosionSound) {
      for(let i in this._api.frameData.explosion_shockwaves) {
        let esw: {
          id: string,
          origin_point: Array<number>,
          radius_meters: number
        } = this._api.frameData.explosion_shockwaves[i]

        // check if ship has been hit by this shockwave already
        if(this.heardExplosionShockwaveIds.indexOf(esw.id) != -1) {
          continue
        }
        // check if ship has been hit by shockwave yet
        const metersDistanceFromCenter = this.getDistanceBetweenCoords(
          {x: ship.coord_x, y:ship.coord_y},
          {x: esw.origin_point[0], y: esw.origin_point[0]}
        ) / this._api.frameData.map_config.units_per_meter
        if(metersDistanceFromCenter <= esw.radius_meters) {
          this.heardExplosionShockwaveIds.push(esw.id)
          this.explosionSound.play()
          setTimeout(() =>{
            this.shipRattlingSound.play()
          }, Math.floor(Math.random() * 50))
        }
        if (
          metersDistanceFromCenter <= (esw.radius_meters + 750)
          && this.heardFastenSeatbeltShockwaveIds.indexOf(esw.id) == -1
        ) {
          this.heardFastenSeatbeltShockwaveIds.push(esw.id)
          this.fastenSeatbeltSound.play()
        }
      }
    }

    if (!this.copilotDeathSoundPlaying && !ship.alive && !ship.explosion_frame) {
      this.copilotDeathSoundPlaying = true
      this.copilotDeathSound.play()
    }
    else if (this.copilotDeathSoundPlaying && ship.explosion_frame) {
      this.copilotDeathSound.pause()
    }

  }

  public runMusicEngine() {

    if(!this.deathMusicPlaying && !this._api.frameData.ship.alive) {
      this.deathMusicPlaying = true
      setTimeout(() => {
        this.deathMusicSound.play()
      }, 1000)
    }

    setTimeout(this.runMusicEngine.bind(this), this.musicEngineInterval)
  }

}
