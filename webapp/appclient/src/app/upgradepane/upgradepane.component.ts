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
  public antiRadarCoatingMissingCoreUpgrades: string[] = []
  public batteryCapacityMissingCoreUpgrades: string[] = []
  public fuelCapacityMissingCoreUpgrades: string[] = []
  public APUEfficiencyMissingCoreUpgrades: string[] = []

  constructor(
    public _api: ApiService,
  ) { }

  ngOnInit(): void {
    setTimeout(()=>{
      this.refreshMissingCoreUpgrades()
    })
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
    if(this._api.frameData.ship.upgrade_summary.ship.anti_radar_coating.current_cost) {
      this.refreshAntiRadarCoatingMissingCoreUpgrades()
    }
    if(this._api.frameData.ship.upgrade_summary.ship.battery_capacity.current_cost) {
      this.refreshBatteryCapacityMissingCoreUpgrades()
    }
    if(this._api.frameData.ship.upgrade_summary.ship.fuel_capacity.current_cost) {
      this.refreshFuelCapacityMissingCoreUpgrades()
    }
    if(this._api.frameData.ship.upgrade_summary.ship.apu_efficiency.current_cost) {
      this.refreshAPUEfficiencyMissingCoreUpgrades()
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
    ).map(missingCoreUpgradeSlug => this._api.frameData.ship.upgrade_summary.core[missingCoreUpgradeSlug].name)
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
  private refreshAntiRadarCoatingMissingCoreUpgrades() {
    this.antiRadarCoatingMissingCoreUpgrades = this.getMissingCoreUpgradeNamesForShipUpgrade("anti_radar_coating")
  }
  private refreshBatteryCapacityMissingCoreUpgrades() {
    this.batteryCapacityMissingCoreUpgrades = this.getMissingCoreUpgradeNamesForShipUpgrade("battery_capacity")
  }
  private refreshFuelCapacityMissingCoreUpgrades() {
    this.fuelCapacityMissingCoreUpgrades = this.getMissingCoreUpgradeNamesForShipUpgrade("fuel_capacity")
  }
  private refreshAPUEfficiencyMissingCoreUpgrades() {
    this.fuelCapacityMissingCoreUpgrades = this.getMissingCoreUpgradeNamesForShipUpgrade("apu_efficiency")
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

  public async btnStartAntiRadarCoatingUpgrade() {
    const command = 'start_ship_upgrade';
    const slug = 'anti_radar_coating';
    await this._api.post("/api/rooms/command", {command, slug});
  }

  public async btnCancelAntiRadarCoatingUpgrade() {
    const command = 'cancel_ship_upgrade';
    const slug = 'anti_radar_coating';
    await this._api.post("/api/rooms/command", {command, slug});
  }

  public async btnStartBatteryCapacityUpgrade() {
    const command = 'start_ship_upgrade';
    const slug = 'battery_capacity';
    await this._api.post("/api/rooms/command", {command, slug});
  }

  public async btnCancelBatteryCapacityUpgrade() {
    const command = 'cancel_ship_upgrade';
    const slug = 'battery_capacity';
    await this._api.post("/api/rooms/command", {command, slug});
  }

  public async btnStartFuelCapacityUpgrade() {
    const command = 'start_ship_upgrade';
    const slug = 'fuel_capacity';
    await this._api.post("/api/rooms/command", {command, slug});
  }

  public async btnCancelFuelCapacityUpgrade() {
    const command = 'cancel_ship_upgrade';
    const slug = 'fuel_capacity';
    await this._api.post("/api/rooms/command", {command, slug});
  }

  public async btnStartAPUEfficiencyUpgrade() {
    const command = 'start_ship_upgrade';
    const slug = 'apu_efficiency';
    await this._api.post("/api/rooms/command", {command, slug});
  }

  public async btnCancelAPUEfficiencyUpgrade() {
    const command = 'cancel_ship_upgrade';
    const slug = 'apu_efficiency';
    await this._api.post("/api/rooms/command", {command, slug});
  }

}
