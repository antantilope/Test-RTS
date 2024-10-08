import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';
import { FormattingService } from '../formatting.service';



export class EngSubPaneData {

  shipMassKG: number
  oreCargoMassKg: number
  oreCargoCapacityMassKg: number

  fuelLevel: number
  fuelCapacity: number
  fuelUsagePerSecond: number | null
  fuelUsagePerMinute: number | null

  batteryPower: number
  batteryCapacity: number
  batteryUsagePerSecond: number | null
batteryUsagePerMinute: number | null
}


@Component({
  selector: 'app-engpane',
  templateUrl: './engpane.component.html',
  styleUrls: ['./engpane.component.css']
})
export class EngpaneComponent implements OnInit {

  private refreshIntervalMS = 500
  public data: EngSubPaneData | null = null
  public lastUpdate: number| null = null
  private destroyed = false

  constructor(
    public _api: ApiService,
    private _formatting: FormattingService
  ) { }

  ngOnInit(): void {
    this.refreshData()
  }

  ngOnDestroy() {
    // Flip this flag so refreshData callbacks stop.
    this.destroyed = true
  }


  refreshData() {
    if(!this._api.frameData.ship || !this._api.frameData.ship.alive) {
      this.data = null

    } else {
      const previousData = this.data
      this.data = {
        shipMassKG: this._api.frameData.ship.mass,
        oreCargoMassKg: this._api.frameData.ship.cargo_ore_mass_kg,
        oreCargoCapacityMassKg: this._api.frameData.ship.cargo_ore_mass_capacity_kg,
        fuelLevel: this._api.frameData.ship.fuel_level,
        fuelCapacity: this._api.frameData.ship.fuel_capacity,
        fuelUsagePerSecond: null,
        fuelUsagePerMinute: null,
        batteryPower: this._api.frameData.ship.battery_power,
        batteryCapacity: this._api.frameData.ship.battery_capacity,
        batteryUsagePerSecond: null,
        batteryUsagePerMinute: null,
      }

      if(previousData !== null) {
        if(this.lastUpdate === null) {
          this.lastUpdate = new Date().valueOf()
        } else {
          const timediff = (new Date().valueOf()) - this.lastUpdate
          this.lastUpdate = new Date().valueOf()
          const fuelDiff = this.data.fuelLevel - previousData.fuelLevel
          const batteryDiff = this.data.batteryPower - previousData.batteryPower
          if(fuelDiff != 0) {
            this.data.fuelUsagePerSecond = Math.round(fuelDiff * 1000 / timediff)
            this.data.fuelUsagePerMinute = Math.round(fuelDiff * 1000 * 60 / timediff)
          }
          if(batteryDiff != 0) {
            this.data.batteryUsagePerSecond = Math.round(batteryDiff * 1000 / timediff)
            this.data.batteryUsagePerMinute = Math.round(batteryDiff * 1000 * 60 / timediff)
          }
        }
      }

    }
    if(!this.destroyed) {
      setTimeout(()=>{
        this.refreshData()
      }, this.refreshIntervalMS)
    }
  }

}
