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
    this._api.emitGameCommand('trade_ore_for_ore_coin', {})
  }

  async btnClickStartFueling() {
    this._api.emitGameCommand('start_fueling', {})
  }

  async btnClickHaltFueling() {
    this._api.emitGameCommand('stop_fueling', {})
  }

  async btnClickBuyMagnetMine() {
    this._api.emitGameCommand('buy_magnet_mine', {})
  }

  async btnClickBuyEMP() {
    this._api.emitGameCommand('buy_emp', {})
  }

  async btnClickBuyHunterDrone() {
    this._api.emitGameCommand('buy_hunter_drone', {})
  }

}
