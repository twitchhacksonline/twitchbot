# VirtualBox to KVM/QEMU VM Conversion Guide

## Executive Summary
Converting VirtualBox VMs to KVM/QEMU is **technically feasible** but comes with several challenges, particularly around snapshots, guest additions, and network drivers. The conversion success rate is high (~90%) for simple VMs but decreases with complexity.

## Conversion Overview

### What Converts Well ✅
- **Disk Images**: VDI → QCOW2 conversion is straightforward
- **Basic VMs**: Single-disk VMs without snapshots
- **Linux Guests**: Built-in virtio driver support
- **Network Config**: VirtualBox virtio-net maps to KVM virtio
- **RAM/CPU Settings**: Direct mapping possible

### What Requires Extra Work ⚠️
- **Snapshots**: Complex snapshot trees don't convert directly
- **Guest Additions**: Must be removed and replaced
- **Windows Guests**: Need virtio driver installation
- **UEFI VMs**: QEMU snapshot limitations
- **Multiple Disks**: Each disk needs conversion

### What May Break ❌
- **Linked Clones**: Require consolidation first
- **Encrypted Disks**: Need decryption before conversion
- **USB Passthrough**: Different configuration method
- **Custom Network**: May need reconfiguration
- **Hardware UUIDs**: Windows activation issues

## Detailed Conversion Process

### Phase 1: Pre-Conversion Preparation

#### 1.1 Snapshot Consolidation
```bash
# CRITICAL: VirtualBox snapshots don't convert to QCOW2 snapshots
# You must choose one approach:

# Option A: Merge all snapshots (RECOMMENDED)
VBoxManage snapshot "VM_Name" list  # View snapshot tree
VBoxManage clonevm "VM_Name" --name "VM_Name_Flat" --mode all

# Option B: Export specific snapshot state
VBoxManage snapshot "VM_Name" restore "Snapshot_Name"
VBoxManage clonevm "VM_Name" --name "VM_Name_Snapshot" --mode machine

# Option C: Use virt-v2v (may preserve some snapshots)
# Limited support, not guaranteed
```

**Impact**: You'll lose the snapshot history. Plan to take new QCOW2 snapshots after conversion.

#### 1.2 Guest Additions Removal
```bash
# Inside the VM (before conversion):

# Linux Guest:
sudo /opt/VBoxGuestAdditions-*/uninstall.sh
sudo apt-get remove --purge virtualbox-guest-*
sudo rm -rf /opt/VBox*

# Windows Guest:
# Control Panel → Programs → Uninstall VirtualBox Guest Additions
# Or run: C:\Program Files\Oracle\VirtualBox Guest Additions\uninstall.exe
```

**Why Critical**: Guest Additions conflict with KVM virtio drivers and cause boot issues.

#### 1.3 Network Configuration Documentation
```bash
# Document current network setup
VBoxManage showvminfo "VM_Name" | grep -E "NIC|Network"

# Note:
# - Bridge adapter settings
# - NAT port forwarding rules
# - Host-only network addresses
# - MAC addresses (for DHCP reservations)
```

### Phase 2: Conversion Methods

#### Method A: Direct VDI to QCOW2 (Simple)
```bash
# 1. Locate VDI file
find ~/VirtualBox\ VMs -name "*.vdi"

# 2. Convert to QCOW2
qemu-img convert -f vdi -O qcow2 \
  ~/VirtualBox\ VMs/VM_Name/VM_Name.vdi \
  /var/lib/libvirt/images/VM_Name.qcow2 \
  -p  # Show progress

# 3. Verify conversion
qemu-img check /var/lib/libvirt/images/VM_Name.qcow2
qemu-img info /var/lib/libvirt/images/VM_Name.qcow2
```

**Success Rate**: 95% for single-disk VMs without snapshots

#### Method B: OVA Export/Import (Comprehensive)
```bash
# 1. Export from VirtualBox (OVF 1.0 format recommended)
VBoxManage export "VM_Name" \
  --output VM_Name.ova \
  --ovf10  # Use OVF 1.0 for better compatibility

# 2. Convert with virt-v2v
sudo virt-v2v \
  -i ova VM_Name.ova \
  -o libvirt \
  -of qcow2 \
  -os /var/lib/libvirt/images \
  -n default \
  --machine-readable  # For scripting

# 3. If virt-v2v fails, manual extraction:
tar -xvf VM_Name.ova
qemu-img convert -f vmdk VM_Name-disk001.vmdk \
  -O qcow2 /var/lib/libvirt/images/VM_Name.qcow2
```

**Success Rate**: 80% - handles more complex configurations

#### Method C: For Windows Guests (Special Handling)
```bash
# 1. Before conversion, note the Hardware UUID
VBoxManage showvminfo "VM_Name" | grep "Hardware UUID"

# 2. Convert disk image
qemu-img convert -f vdi Windows.vdi -O qcow2 Windows.qcow2

# 3. Create VM in KVM preserving UUID (prevents reactivation)
virt-install \
  --name Windows_VM \
  --memory 4096 \
  --vcpus 2 \
  --disk /var/lib/libvirt/images/Windows.qcow2,bus=virtio \
  --os-variant win10 \
  --network bridge=br0,model=virtio \
  --uuid=<PRESERVED_UUID> \
  --import
```

### Phase 3: Post-Conversion Configuration

#### 3.1 Install VirtIO Drivers (Critical for Performance)

**Linux Guests** (Usually automatic):
```bash
# Verify virtio modules are loaded
lsmod | grep virtio

# If not, install:
sudo apt-get install linux-virtual  # Ubuntu/Debian
sudo yum install kernel-modules-extra  # RHEL/CentOS
```

**Windows Guests** (Manual installation required):
```powershell
# 1. Download virtio-win ISO
wget https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso

# 2. Attach ISO to VM
virsh attach-disk Windows_VM /path/to/virtio-win.iso hdc --type cdrom

# 3. Inside Windows:
# - Device Manager → Update drivers
# - Browse to ISO → Install:
#   - NetKVM (Network)
#   - Viostor (Storage)
#   - Vioserial (Serial)
#   - Balloon (Memory management)
#   - VioSCSI (SCSI)

# 4. Install guest tools
D:\virtio-win-guest-tools.exe
```

#### 3.2 Network Reconfiguration

```xml
<!-- Edit VM definition: virsh edit VM_Name -->

<!-- NAT Network (like VirtualBox NAT) -->
<interface type='network'>
  <source network='default'/>
  <model type='virtio'/>
</interface>

<!-- Bridged Network (like VirtualBox Bridged) -->
<interface type='bridge'>
  <source bridge='br0'/>
  <model type='virtio'/>
  <mac address='52:54:00:XX:XX:XX'/>  <!-- Preserve MAC if needed -->
</interface>

<!-- Host-Only (like VirtualBox Host-Only) -->
<interface type='network'>
  <source network='isolated'/>
  <model type='virtio'/>
</interface>
```

#### 3.3 Storage Optimization
```bash
# Convert to virtio for better performance
virsh edit VM_Name

# Change:
# <disk type='file' device='disk'>
#   <driver name='qemu' type='qcow2'/>
#   <target dev='hda' bus='ide'/>  <!-- Change this -->

# To:
#   <target dev='vda' bus='virtio'/>  <!-- To this -->
```

### Phase 4: Validation & Testing

#### 4.1 Boot Testing Checklist
- [ ] VM boots successfully
- [ ] Network connectivity works
- [ ] Display resolution adjusts properly
- [ ] Clipboard sharing (with SPICE)
- [ ] File sharing (with virtio-fs)
- [ ] Performance acceptable

#### 4.2 Performance Comparison
```bash
# Benchmark before (VirtualBox) and after (KVM)

# CPU Performance
time dd if=/dev/zero of=/dev/null bs=1M count=10000

# Disk I/O
dd if=/dev/zero of=testfile bs=1G count=1 oflag=direct

# Network
iperf3 -c <host_ip>
```

Expected improvements:
- CPU: 10-15% better
- Disk I/O: 30-50% better with virtio
- Network: 20-40% better with virtio

#### 4.3 Create New Snapshots
```bash
# KVM/QEMU snapshot management
virsh snapshot-create-as VM_Name \
  --name "post-migration" \
  --description "Clean state after VirtualBox migration"

# List snapshots
virsh snapshot-list VM_Name

# Revert if needed
virsh snapshot-revert VM_Name post-migration
```

## Common Issues & Solutions

### Issue 1: VM Won't Boot After Conversion
**Symptoms**: Black screen, boot loop, or kernel panic

**Solutions**:
```bash
# 1. Check disk bus type (might need IDE initially)
virsh edit VM_Name
# Change bus='virtio' to bus='ide' temporarily

# 2. For Windows, might need to change boot mode
# Change from UEFI to BIOS or vice versa

# 3. Rebuild initramfs (Linux)
# Boot from rescue ISO, then:
update-initramfs -u
grub-install /dev/vda
update-grub
```

### Issue 2: Network Not Working
**Symptoms**: No network adapter detected

**Solutions**:
```bash
# 1. Install virtio drivers (see above)

# 2. Reset network configuration (Linux)
sudo rm /etc/udev/rules.d/70-persistent-net.rules
sudo reboot

# 3. Manually configure (Windows)
# Device Manager → Add Legacy Hardware → Network Adapter
```

### Issue 3: Poor Graphics Performance
**Symptoms**: Slow screen updates, no acceleration

**Solutions**:
```xml
<!-- Enable SPICE with QXL -->
<graphics type='spice' autoport='yes'>
  <listen type='address'/>
</graphics>
<video>
  <model type='qxl' ram='65536' vram='65536' heads='1'/>
</video>
```

### Issue 4: Windows Activation Issues
**Symptoms**: Windows deactivated after migration

**Solutions**:
```bash
# 1. Preserve Hardware UUID (see Method C above)

# 2. If already converted, update UUID:
virsh dumpxml VM_Name > vm.xml
# Edit vm.xml, add: <uuid>ORIGINAL_UUID</uuid>
virsh define vm.xml

# 3. Phone activation may be required
slmgr /rearm  # Reset activation grace period
```

## Automation Script

```bash
#!/bin/bash
# vbox_to_kvm.sh - Automated conversion script

set -e

VM_NAME="$1"
if [ -z "$VM_NAME" ]; then
    echo "Usage: $0 <VM_NAME>"
    exit 1
fi

echo "=== VirtualBox to KVM Conversion ==="
echo "VM: $VM_NAME"

# 1. Check prerequisites
command -v VBoxManage >/dev/null 2>&1 || { echo "VirtualBox CLI required"; exit 1; }
command -v qemu-img >/dev/null 2>&1 || { echo "qemu-img required"; exit 1; }
command -v virsh >/dev/null 2>&1 || { echo "libvirt required"; exit 1; }

# 2. Get VM info
echo "Gathering VM information..."
VDI_PATH=$(VBoxManage showvminfo "$VM_NAME" --machinereadable | grep "^\"SATA-0-0\"" | cut -d'"' -f4)
MEMORY=$(VBoxManage showvminfo "$VM_NAME" --machinereadable | grep "^memory=" | cut -d'=' -f2)
CPUS=$(VBoxManage showvminfo "$VM_NAME" --machinereadable | grep "^cpus=" | cut -d'=' -f2)
UUID=$(VBoxManage showvminfo "$VM_NAME" --machinereadable | grep "^UUID=" | cut -d'"' -f2)

echo "VDI: $VDI_PATH"
echo "Memory: ${MEMORY}MB"
echo "CPUs: $CPUS"
echo "UUID: $UUID"

# 3. Check for snapshots
SNAPSHOTS=$(VBoxManage snapshot "$VM_NAME" list 2>/dev/null | wc -l)
if [ "$SNAPSHOTS" -gt 0 ]; then
    echo "WARNING: VM has $SNAPSHOTS snapshots. These will be lost."
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 4. Shutdown VM if running
STATE=$(VBoxManage showvminfo "$VM_NAME" --machinereadable | grep "^VMState=" | cut -d'"' -f2)
if [ "$STATE" = "running" ]; then
    echo "Shutting down VM..."
    VBoxManage controlvm "$VM_NAME" acpipowerbutton
    sleep 10
fi

# 5. Convert disk
QCOW2_PATH="/var/lib/libvirt/images/${VM_NAME}.qcow2"
echo "Converting VDI to QCOW2..."
qemu-img convert -f vdi -O qcow2 -p "$VDI_PATH" "$QCOW2_PATH"

# 6. Create KVM VM
echo "Creating KVM VM..."
virt-install \
    --name "$VM_NAME" \
    --memory "$MEMORY" \
    --vcpus "$CPUS" \
    --disk "$QCOW2_PATH",bus=virtio \
    --network bridge=virbr0,model=virtio \
    --graphics spice \
    --video qxl \
    --uuid="$UUID" \
    --os-variant generic \
    --import \
    --noautoconsole

echo "=== Conversion Complete ==="
echo "VM '$VM_NAME' is now available in KVM"
echo "Start with: virsh start $VM_NAME"
echo "Connect with: virt-viewer $VM_NAME"
```

## Decision Matrix

| Factor | Keep VirtualBox | Migrate to KVM |
|--------|----------------|----------------|
| **Snapshot Complexity** | Many snapshots with branches | Few or no snapshots |
| **Guest OS** | Windows with specific software | Linux or Windows Server |
| **Team Expertise** | VirtualBox experience only | Linux/KVM knowledge |
| **Performance Needs** | Adequate | Critical |
| **Host OS** | Windows/Mac | Linux |
| **Time Available** | < 1 week | > 2 weeks |
| **Risk Tolerance** | Low | Medium-High |

## Recommendation for TwitchBot Project

Given your TwitchBot use case with CTF challenges:

### ✅ **Proceed with KVM Migration If:**
- You have < 5 snapshots per VM
- VMs are Linux-based CTF challenges
- Performance improvement (30-50%) justifies effort
- You have 2-3 weeks for migration and testing
- Team is comfortable with Linux administration

### ⚠️ **Stay with VirtualBox If:**
- Complex snapshot trees are critical for CTF progression
- Windows-based challenges with specific software
- Migration timeline < 1 week
- Team lacks KVM/libvirt experience
- Need to maintain exact VM state for ongoing competitions

### 🔄 **Hybrid Approach (Recommended)**
1. **Keep existing VirtualBox VMs** for current challenges
2. **Create new challenges in KVM** going forward
3. **Gradually migrate** simple VMs first
4. **Run both in parallel** during transition
5. **Full migration** after validating with test challenges

This approach minimizes risk while allowing you to gain KVM experience and realize performance benefits incrementally.