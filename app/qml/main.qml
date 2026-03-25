import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

// ── Application window ────────────────────────────────────────────────────────
// Full-bleed camera image; floating chrome scales with window size / avoids overlap.
ApplicationWindow {
    id: win
    title:         "Dental Imaging System"
    width:         1280
    height:        720
    minimumWidth:  720
    minimumHeight: 480
    visible:       true
    color:         "#0d0f14"

    // ── Responsive chrome (margins + rail width + compact breakpoints) ───
    readonly property bool uiCompact: width < 1180
    readonly property bool uiNarrow:  width < 920
    readonly property bool uiShort:   height < 700
    readonly property real marginH:   Math.max(10, Math.min(18, width * 0.016))
    readonly property real marginV:   Math.max(8, Math.min(14, height * 0.014))
    readonly property real railW:     uiNarrow ? 66 : 76
    property string lastCapturePath: ""
    property int lastCaptureW: 0
    property int lastCaptureH: 0

    readonly property real bottomBarTargetW: {
        const frac = uiNarrow ? 0.90 : 0.68
        const cap = Math.min(920, Math.floor(width * frac))
        const gap = 16
        // Keep bar from overlapping the right rail when centered
        const overlapMax = rightRail.x > gap
            ? Math.floor(2 * rightRail.x - width - 2 * gap)
            : Math.floor(width - railW - marginH * 2 - 32)
        return Math.max(240, Math.min(cap, overlapMax))
    }

    Item {
        id: cameraArea
        anchors.fill: parent
        z: 0

        Image {
            id: camera
            anchors.fill: parent
            source:       "image://camera/frame?" + bridge.frameCounter
            fillMode:     Image.PreserveAspectCrop
            cache:        false
            smooth:       true
            asynchronous: false

            Rectangle {
                anchors.fill: parent
                color:        "#0d0f14"
                visible:      camera.status !== Image.Ready
                Text {
                    anchors.centerIn: parent
                    text:  "Waiting for camera…"
                    color: "#404055"
                    font.pixelSize: win.uiCompact ? 15 : 18
                }
            }
        }

        // Drag to pan when zoomed (phone-style)
        MouseArea {
            id: panArea
            z: 1
            anchors.fill: parent
            enabled: bridge.connected && bridge.zoom > 2
            acceptedButtons: Qt.LeftButton
            hoverEnabled: true
            cursorShape: !enabled ? Qt.ArrowCursor
                : (pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor)

            property real ldx: 0
            property real ldy: 0

            onPressed: function (mouse) {
                ldx = mouse.x
                ldy = mouse.y
            }
            onPositionChanged: function (mouse) {
                if (!pressed)
                    return
                var dx = mouse.x - ldx
                var dy = mouse.y - ldy
                ldx = mouse.x
                ldy = mouse.y
                bridge.applyPreviewPanDelta(dx, dy, width, height)
            }
            onDoubleClicked: function (/*mouse*/) {
                bridge.resetPreviewPan()
            }
        }

        // Minimap: full-frame thumb + viewport rectangle
        // (Must anchor to parent/sibling only — bottomBar is not parent of this Item.)
        Rectangle {
            id: minimapChrome
            z: 4
            readonly property real desiredHeight: Math.max(40, Math.round(width * Math.max(0.2, bridge.minimapAspectRatio)))
            readonly property real bottomInset: bottomBar.height + Math.max(12, win.marginV + (win.uiShort ? 4 : 10)) + 10
            readonly property real topClearance: topBar.y + topBar.height + 10
            readonly property real availableHeight: Math.max(0, parent.height - bottomInset - topClearance)

            visible: bridge.connected && bridge.zoom > 2 && availableHeight >= 40
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            anchors.leftMargin: Math.max(12, win.marginH)
            anchors.bottomMargin: bottomInset
            width: win.uiNarrow ? 96 : 128
            height: Math.min(desiredHeight, availableHeight)
            radius: 10
            color: Qt.rgba(0, 0, 0, 0.5)
            border.width: 1
            border.color: Qt.rgba(1, 1, 1, 0.35)
            clip: true

            Item {
                id: miniInner
                anchors.fill: parent
                anchors.margins: 3
                clip: true

                MouseArea {
                    id: minimapDragArea
                    anchors.fill: parent
                    enabled: minimapChrome.visible
                    acceptedButtons: Qt.LeftButton
                    hoverEnabled: true
                    cursorShape: pressed ? Qt.ClosedHandCursor : Qt.PointingHandCursor

                    function updatePan(mx, my) {
                        if (width <= 0 || height <= 0)
                            return
                        var nx = Math.max(0.0, Math.min(1.0, mx / width))
                        var ny = Math.max(0.0, Math.min(1.0, my / height))
                        bridge.setPreviewPanFromMinimap(nx, ny)
                    }

                    onPressed: function (mouse) {
                        updatePan(mouse.x, mouse.y)
                    }
                    onPositionChanged: function (mouse) {
                        if (pressed)
                            updatePan(mouse.x, mouse.y)
                    }
                    onDoubleClicked: function (/*mouse*/) {
                        bridge.resetPreviewPan()
                    }
                }

                Image {
                    anchors.fill: parent
                    fillMode: Image.Stretch
                    source: "image://camera/overview?" + bridge.frameCounter
                    asynchronous: false
                    smooth: true
                }

                Rectangle {
                    x: parent.width * bridge.minimapViewportX
                    y: parent.height * bridge.minimapViewportY
                    width: parent.width * bridge.minimapViewportWidth
                    height: parent.height * bridge.minimapViewportHeight
                    color: "transparent"
                    border.width: 1.5
                    border.color: Qt.rgba(1, 1, 1, 0.92)
                    radius: 2
                }
            }
        }
    }

    // ── Top bar ───────────────────────────────────────────────────────────
    TopBar {
        id: topBar
        z: 20
        anchors {
            top: parent.top
            left: parent.left
            right: parent.right
            topMargin: marginV + (uiShort ? 2 : 4)
            leftMargin: marginH
            rightMargin: marginH
        }
        height: uiCompact ? 50 : 56
    }

    // ── Bottom bar (width capped vs. right rail) ────────────────────────────
    BottomBar {
        id: bottomBar
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: Math.max(12, marginV + (uiShort ? 4 : 10))
        width: win.bottomBarTargetW
        height: uiCompact ? 70 : 78
    }

    // ── Right rail ──────────────────────────────────────────────────────────
    RightRail {
        id: rightRail
        z: 10
        anchors {
            top: topBar.bottom
            right: parent.right
            bottom: bottomBar.top
            // Clear gap under top bar so rail capsules never meet the header edge
            topMargin: Math.max(16, marginV + (uiShort ? 10 : 14))
            rightMargin: marginH + 4
            bottomMargin: uiShort ? 10 : 14
        }
        width: win.railW
    }

    // ── Floating panels (stay inside window next to rail) ───────────────────
    ImageSettingsPanel {
        id: imgPanel
        x: Math.max(8, Math.min(rightRail.x - width - 10, win.width - width - marginH))
        y: topBar.y + topBar.height + 10
        maxPanelHeight: win.height - topBar.y - topBar.height - 12 - bottomBar.height - 32
    }

    SettingsPanel {
        id: settingsPanel
        x: Math.max(8, Math.min(rightRail.x - width - 10, win.width - width - marginH))
        y: topBar.y + topBar.height + 10
        maxPanelHeight: win.height - topBar.y - topBar.height - 12 - bottomBar.height - 32
    }

    Toast {
        id: toast
        z: 200
        anchors {
            horizontalCenter: parent.horizontalCenter
            bottom:           parent.bottom
            bottomMargin:     bottomBar.height + Math.max(24, marginV + 14)
        }
    }

    CaptureSavedModal {
        id: captureModal
        capturePath: win.lastCapturePath
        captureW: win.lastCaptureW
        captureH: win.lastCaptureH
    }

    Connections {
        target: bridge
        function onToastRequested(message) { toast.show(message) }
        function onCaptureSaved(path, width, height) {
            win.lastCapturePath = path
            win.lastCaptureW = width
            win.lastCaptureH = height
            captureModal.open()
        }
        function onCaptureFailed(message) {
            // Keep toast for failures; modal is for success acknowledgement.
        }
    }

    Item {
        anchors.fill: parent
        focus: true
        Keys.onPressed: (e) => {
            if (e.key === Qt.Key_Space) { bridge.onCapture(); e.accepted = true }
            if (e.key === Qt.Key_Escape && bridge.imageSettingsVisible) {
                bridge.onImageSettingsToggled(false); e.accepted = true
            }
            if (e.key === Qt.Key_Escape && bridge.settingsPanelVisible) {
                bridge.onSettingsPanelToggled(false); e.accepted = true
            }
        }
    }
}
