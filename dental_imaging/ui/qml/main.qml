import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Effects

Item {
    id: root
    focus: true

    // ── Palette ────────────────────────────────────────────────────────────
    readonly property color chromeBg:     Qt.rgba(0.08, 0.09, 0.11, 0.72)
    readonly property color chromeBorder: Qt.rgba(1, 1, 1, 0.10)
    readonly property color textPrimary:  "#ffffff"
    readonly property color textMuted:    "#a0a0b0"
    readonly property color accent:       "#5aaaff"
    readonly property color success:      "#5aba82"

    // ── Layout constants (scale with window) ───────────────────────────────
    readonly property int topBarH:   Math.max(56, Math.round(height * 0.064))
    readonly property int railW:     Math.max(80, Math.round(width  * 0.076))
    readonly property int bottomBarH:Math.max(88, Math.round(height * 0.098))
    readonly property int panelW:    Math.min(340, Math.round(width  * 0.30))
    readonly property real sp:       Math.max(1,  Math.round(height  / 540))  // spacing unit

    // ── Full-bleed camera image ────────────────────────────────────────────
    Image {
        id: cameraImage
        anchors.fill: parent
        // Reload every time frameId changes (no cache)
        source: "image://camera/frame?" + bridge.frameId
        cache:  false
        asynchronous: true
        smooth: true
        fillMode: Image.PreserveAspectCrop
    }

    // Placeholder when no camera
    Rectangle {
        anchors.fill: parent
        visible: !bridge.captureEnabled
        color: "#0c0d10"
        Text {
            anchors.centerIn: parent
            text: "No camera signal"
            color: "#44454a"
            font.pixelSize: Math.max(14, root.height / 32)
            font.family: "Segoe UI"
        }
    }

    // ── Top bar ────────────────────────────────────────────────────────────
    TopBar {
        id: topBar
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: root.topBarH
        chromeBg:     root.chromeBg
        chromeBorder: root.chromeBorder
        brandTitle:   bridge.brandTitle
        statsText:    bridge.statsText
        connected:    bridge.cameraConnected
        onPowerClicked: bridge.powerClicked()
    }

    // ── Right tool rail ────────────────────────────────────────────────────
    RightRail {
        id: rightRail
        anchors {
            right:  parent.right
            top:    topBar.bottom
            bottom: bottomBar.top
        }
        width: root.railW
        chromeBg:      root.chromeBg
        chromeBorder:  root.chromeBorder
        captureEnabled: bridge.captureEnabled
        autoColorActive: bridge.autoColorActive
        roiModeActive:   bridge.roiModeActive

        onFlipH:       bridge.flipH()
        onFlipV:       bridge.flipV()
        onRotateCW:    bridge.rotateCW()
        onRotateCCW:   bridge.rotateCCW()
        onCapture:     bridge.capture()
        onRecenterROI: bridge.recenterROI()

        onImageSettingsToggled: function(open) {
            if (open && settingsPanel.visible) settingsPanel.visible = false
            imageSettingsPanel.visible = open
        }
        onSettingsToggled: function(open) {
            if (open && imageSettingsPanel.visible) {
                imageSettingsPanel.visible = false
                rightRail.imageSettingsChecked = false
            }
            if (open) settingsPanel.openPanel()
            else      settingsPanel.visible = false
        }
        onAutoColorToggled:  function(on) { bridge.autoColorToggled(on) }
        onRoiModeToggled:    function(on) { bridge.roiModeToggled(on) }
    }

    // ── Bottom control bar ─────────────────────────────────────────────────
    BottomBar {
        id: bottomBar
        anchors {
            left:   parent.left
            right:  rightRail.left
            bottom: parent.bottom
        }
        height: root.bottomBarH
        chromeBg:     root.chromeBg
        chromeBorder: root.chromeBorder
        brightness:   bridge.brightness
        zoom:         bridge.zoom
        activePreset: bridge.activePreset

        onBrightnessEdited: function(v) { bridge.setBrightness(v) }
        onZoomEdited:       function(v) { bridge.setZoom(v) }
        onPresetClicked:     function(n) { bridge.presetClicked(n) }
        onPresetSaveReq:     function(n) { bridge.presetSaveRequested(n) }
    }

    // ── ROI overlay ────────────────────────────────────────────────────────
    ROIOverlay {
        id: roiOverlay
        anchors { left: parent.left; right: rightRail.left; top: topBar.bottom; bottom: bottomBar.top }
        visible: bridge.roiModeActive
        imageW: cameraImage.paintedWidth
        imageH: cameraImage.paintedHeight
        imageX: (width  - cameraImage.paintedWidth)  / 2
        imageY: (height - cameraImage.paintedHeight) / 2
    }

    // ── Image Settings floating panel ──────────────────────────────────────
    ImageSettingsPanel {
        id: imageSettingsPanel
        visible: false
        width:  root.panelW
        anchors {
            right:  rightRail.left
            top:    topBar.bottom
            bottom: bottomBar.top
            rightMargin: 12
        }

        onClose: {
            visible = false
            rightRail.imageSettingsChecked = false
        }
        onResetClicked: bridge.resetImageSettings()
        onExposureChanged:     function(v) { bridge.setExposure(v) }
        onGainChanged:         function(v) { bridge.setGain(v) }
        onWhiteBalanceChanged: function(v) { bridge.setWhiteBalance(v) }
        onContrastChanged:     function(v) { bridge.setContrast(v) }
        onSaturationChanged:   function(v) { bridge.setSaturation(v) }
        onWarmthChanged:       function(v) { bridge.setWarmth(v) }
        onTintChanged:         function(v) { bridge.setTint(v) }

        onVisibleChanged: {
            if (visible) {
                var vals = bridge.getImageSettingsValues()
                syncValues(vals)
            }
        }
    }

    // ── Settings floating panel ────────────────────────────────────────────
    SettingsPanel {
        id: settingsPanel
        visible: false
        width:  root.panelW
        anchors {
            right:  rightRail.left
            top:    topBar.bottom
            bottom: bottomBar.top
            rightMargin: 12
        }

        function openPanel() {
            var vals = bridge.getSettingsValues()
            syncValues(vals)
            visible = true
        }

        onClose: {
            visible = false
            rightRail.settingsChecked = false
        }
        onShowGridChanged:      function(v) { bridge.setShowGrid(v) }
        onShowCrosshairChanged: function(v) { bridge.setShowCrosshair(v) }
        onAutoScaleChanged:     function(v) { bridge.setAutoScale(v) }
        onExportScopeChanged:   function(v) { bridge.setExportScope(v) }
        onCaptureFormatChanged: function(v) { bridge.setCaptureFormat(v) }
        onJpegQualityChanged:   function(v) { bridge.setJpegQuality(v) }
        onCaptureModeChanged:   function(v) { bridge.setCaptureMode(v) }
        onBurstDelayChanged:    function(v) { bridge.setBurstDelay(v) }
        onCameraSoundChanged:   function(v) { bridge.setCameraSound(v) }
        onStorageTargetChanged: function(v) { bridge.setStorageTarget(v) }
    }

    // ── Connections: Python → QML ──────────────────────────────────────────
    Connections {
        target: bridge
        function onImageSettingsChanged(vals) { imageSettingsPanel.syncValues(vals) }
        function onToastRequested(msg, ms) { toast.show(msg, ms) }
        function onStatusChanged(msg) { statusBar.text = msg }
    }

    // ── Toast notification ─────────────────────────────────────────────────
    Toast {
        id: toast
        anchors {
            horizontalCenter: parent.horizontalCenter
            bottom: bottomBar.top
            bottomMargin: 16
        }
    }

    // ── Status bar (dev/debug) ─────────────────────────────────────────────
    Text {
        id: statusBar
        anchors { bottom: bottomBar.top; left: parent.left; leftMargin: 8; bottomMargin: 2 }
        text: bridge.status
        color: "#606068"
        font.pixelSize: 10
        font.family: "Consolas, monospace"
        visible: false  // enable during development
    }
}
