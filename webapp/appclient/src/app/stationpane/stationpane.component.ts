import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-stationpane',
  templateUrl: './stationpane.component.html',
  styleUrls: ['./stationpane.component.css']
})
export class StationpaneComponent implements OnInit {

  stationName: string

  constructor(
    public _api: ApiService,
  ) { }

  ngOnInit(): void {
    this.stationName = this._api.frameData.space_stations.find(
      st => st.uuid == this._api.frameData.ship.docked_at_station
    ).name
  }

  async btnClickTradeOreForOreCoin() {
    await this._api.post(
      "/api/rooms/command",
      {command:'trade_ore_for_ore_coin'},
    )
  }

  async btnClickStartFueling() {
    await this._api.post(
      "/api/rooms/command",
      {command:'start_fueling'},
    )
  }

  async btnClickHaltFueling() {
    await this._api.post(
      "/api/rooms/command",
      {command:'stop_fueling'},
    )
  }

  async btnClickBuyMagnetMine() {
    await this._api.post(
      "/api/rooms/command",
      {command:'buy_magnet_mine'},
    )
  }

  async btnClickBuyEMP() {
    await this._api.post(
      "/api/rooms/command",
      {command:'buy_emp'},
    )
  }

  async btnClickBuyHunterDrone() {
    await this._api.post(
      "/api/rooms/command",
      {command:'buy_hunter_drone'},
    )
  }

}
