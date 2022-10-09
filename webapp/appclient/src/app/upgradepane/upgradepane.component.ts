import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-upgradepane',
  templateUrl: './upgradepane.component.html',
  styleUrls: ['./upgradepane.component.css']
})
export class UpgradepaneComponent implements OnInit {

  private refreshMissingCoreUpgradesInterval = 700;
  // Array of missing core upgrades needed to start ship upgrades
  public engineNewtonsMissingCoreUpgrades: string[] = []
  public oreCapacityMissingCoreUpgrades: string[] = []

  constructor(
    public _api: ApiService,
  ) { }

  ngOnInit(): void {
    setTimeout(()=>{
      this.refreshMissingCoreUpgrades()
    }, this.refreshMissingCoreUpgradesInterval)
  }

  private refreshMissingCoreUpgrades() {
    if(this._api.frameData.ship.upgrade_summary.ship.engine_newtons.current_cost) {
      this.refreshEngineNewtonsMissingCoreUpgrades()
    }
    if(this._api.frameData.ship.upgrade_summary.ship.ore_capacity.current_cost) {
      this.refreshOreCapacityMissingCoreUpgrades()
    }
    setTimeout(()=>{
      this.refreshMissingCoreUpgrades()
    }, this.refreshMissingCoreUpgradesInterval)
  }
  private refreshEngineNewtonsMissingCoreUpgrades() {
    this.engineNewtonsMissingCoreUpgrades = (
      this._api.frameData.ship.upgrade_summary.ship.engine_newtons.current_cost.core_upgrade_slugs.filter(coreUpgrdeSlug => {
        return this._api.frameData.ship.upgrade_summary.core[coreUpgrdeSlug].current_level == 0
      })
    ).map(missingSlug => this._api.frameData.ship.upgrade_summary.core[missingSlug].name)
  }
  private refreshOreCapacityMissingCoreUpgrades() {
    this.oreCapacityMissingCoreUpgrades = (
      this._api.frameData.ship.upgrade_summary.ship.ore_capacity.current_cost.core_upgrade_slugs.filter(coreUpgrdeSlug => {
        return this._api.frameData.ship.upgrade_summary.core[coreUpgrdeSlug].current_level == 0
      })
    ).map(missingSlug => this._api.frameData.ship.upgrade_summary.core[missingSlug].name)
  }

  // Core Upgrades
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

  // Ship Upgrades
  public async btnStartEngineNewtonsUpgrade() {
    const command = 'start_ship_upgrade';
    const slug = 'engine_newtons';
    await this._api.post("/api/rooms/command", {command, slug});
  }

  public async btnCancelEngineNewtonsUpgrade() {
    const command = 'cancel_ship_upgrade';
    const slug = 'engine_newtons';
    await this._api.post("/api/rooms/command", {command, slug});
  }

  public async btnStartOreCapacityUpgrade() {
    const command = 'start_ship_upgrade';
    const slug = 'ore_capacity';
    await this._api.post("/api/rooms/command", {command, slug});
  }

  public async btnCancelOreCapacityUpgrade() {
    const command = 'cancel_ship_upgrade';
    const slug = 'ore_capacity';
    await this._api.post("/api/rooms/command", {command, slug});
  }

}
