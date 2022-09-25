import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-upgradepane',
  templateUrl: './upgradepane.component.html',
  styleUrls: ['./upgradepane.component.css']
})
export class UpgradepaneComponent implements OnInit {

  constructor(
    public _api: ApiService,
  ) { }

  ngOnInit(): void {
  }

  public async btnStartAdvancedElectronicsUpgrade() {
    const command = 'start_core_upgrade';
    const slug = 'advanced_electronics';
    await this._api.post("/api/rooms/command", {command, slug});
  }

  public async btnCancelAdvancedElectronicsUpgrade() {
    const command = 'cancel_core_upgrade';
    const slug = 'advanced_electronics';
    await this._api.post("/api/rooms/command", {command, slug});
  }

  public async btnStartTitaniumAllowHullUpgrade() {
    const command = 'start_core_upgrade';
    const slug = 'titanium_alloy_hull';
    await this._api.post("/api/rooms/command", {command, slug});
  }

  public async btnCancelTitaniumAllowHullUpgrade() {
    const command = 'cancel_core_upgrade';
    const slug = 'titanium_alloy_hull';
    await this._api.post("/api/rooms/command", {command, slug});
  }

  public async btnStartLiquidNitrogenCoolingUpgrade() {
    const command = 'start_core_upgrade';
    const slug = 'liquid_nitrogen_cooling';
    await this._api.post("/api/rooms/command", {command, slug});
  }

  public async btnCancelLiquidNitrogenCoolingUpgrade() {
    const command = 'cancel_core_upgrade';
    const slug = 'liquid_nitrogen_cooling';
    await this._api.post("/api/rooms/command", {command, slug});
  }

}
