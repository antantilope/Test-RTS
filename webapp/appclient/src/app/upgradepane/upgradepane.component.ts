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
  public scannerRangeMissingCoreUpgrades: string[] = []
  public scannerLockTraversalMissingCoreUpgrades: string[] = []
  public scannerRadarSensitivityMissingCoreUpgrades: string[] = []

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
    if(this._api.frameData.ship.upgrade_summary.ship.scanner_range.current_cost) {
      this.refreshScannerRangeMissingCoreUpgrades()
    }
    if(this._api.frameData.ship.upgrade_summary.ship.scanner_lock_traversal.current_cost) {
      this.refreshScannerLockTraversalMissingCoreUpgrades()
    }
    if(this._api.frameData.ship.upgrade_summary.ship.radar_sensitivity.current_cost) {
      this.refreshScannerRadarSensitivityMissingCoreUpgrades()
    }
    setTimeout(()=>{
      this.refreshMissingCoreUpgrades()
    }, this.refreshMissingCoreUpgradesInterval)
  }

  private getMissingCoreUpgradeNamesForShipUpgrade(shipUpgradeSlug: string): string[] {
    return (
      this._api.frameData.ship.upgrade_summary.ship[shipUpgradeSlug].current_cost.core_upgrade_slugs.filter(coreUpgrdeSlug => {
        return this._api.frameData.ship.upgrade_summary.core[coreUpgrdeSlug].current_level == 0
      })
    ).map(missingSlug => this._api.frameData.ship.upgrade_summary.core[missingSlug].name)
  }
  private refreshEngineNewtonsMissingCoreUpgrades() {
    this.engineNewtonsMissingCoreUpgrades = this.getMissingCoreUpgradeNamesForShipUpgrade("engine_newtons")
  }
  private refreshOreCapacityMissingCoreUpgrades() {
    this.oreCapacityMissingCoreUpgrades = this.getMissingCoreUpgradeNamesForShipUpgrade("ore_capacity")
  }
  private refreshScannerRangeMissingCoreUpgrades() {
    this.scannerRangeMissingCoreUpgrades = this.getMissingCoreUpgradeNamesForShipUpgrade("scanner_range")
  }
  private refreshScannerLockTraversalMissingCoreUpgrades() {
    this.scannerLockTraversalMissingCoreUpgrades = this.getMissingCoreUpgradeNamesForShipUpgrade("scanner_lock_traversal")
  }
  private refreshScannerRadarSensitivityMissingCoreUpgrades() {
    this.scannerRadarSensitivityMissingCoreUpgrades = this.getMissingCoreUpgradeNamesForShipUpgrade("radar_sensitivity")
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

  public async btnStartScannerRangeUpgrade() {
    const command = 'start_ship_upgrade';
    const slug = 'scanner_range';
    await this._api.post("/api/rooms/command", {command, slug});
  }

  public async btnCancelScannerRangeUpgrade() {
    const command = 'cancel_ship_upgrade';
    const slug = 'scanner_range';
    await this._api.post("/api/rooms/command", {command, slug});
  }

  public async btnStartScannerLockTraversalUpgrade() {
    const command = 'start_ship_upgrade';
    const slug = 'scanner_lock_traversal';
    await this._api.post("/api/rooms/command", {command, slug});
  }

  public async btnCancelScannerLockTraversalUpgrade() {
    const command = 'cancel_ship_upgrade';
    const slug = 'scanner_lock_traversal';
    await this._api.post("/api/rooms/command", {command, slug});
  }

  public async btnStartScannerRadarSensitivityUpgrade() {
    const command = 'start_ship_upgrade';
    const slug = 'radar_sensitivity';
    await this._api.post("/api/rooms/command", {command, slug});
  }

  public async btnCancelScannerRadarSensitivityUpgrade() {
    const command = 'cancel_ship_upgrade';
    const slug = 'radar_sensitivity';
    await this._api.post("/api/rooms/command", {command, slug});
  }


}
