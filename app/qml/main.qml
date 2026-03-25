import QtQuick
import QtQuick.Controls

// ── Application window ────────────────────────────────────────────────────────
// Full-bleed camera image fills the background.
// Top / right / bottom chrome are floating “pill” panels (Occuscope-style margins).
// Image-settings / settings modals float above everything.
ApplicationWindow {
    id: win
    title:        "Dental Imaging System"
    width:        1900
    height:       1080
    minimumWidth: 1280
    minimumHeight: 960
    visible:      true
    color:        "#0d0f14"

    // ── Camera / placeholder image ─────────────────────────────────────────
    Image {
        id: camera
        anchors.fill: parent
        source:       "image://camera/frame?" + bridge.frameCounter
        fillMode:     Image.PreserveAspectCrop
        cache:        false
        smooth:       true
        asynchronous: false

        // Dark backdrop while waiting for the first frame
        Rectangle {
            anchors.fill: parent
            color:        "#0d0f14"
            visible:      camera.status !== Image.Ready
            Text {
                anchors.centerIn: parent
                text:  "Waiting for camera…"
                color: "#404055"
                font.pixelSize: 18
            }
        }
    }

    // ── Top bar (full width, inset from edges) ─────────────────────────────
    TopBar {
        id: topBar
        anchors {
            top: parent.top
            left: parent.left
            right: parent.right
            topMargin: 12
            leftMargin: 14
            rightMargin: 14
        }
        height: 56
    }

    // ── Bottom bar — centered capsule ~⅔ width ───────────────────────────
    BottomBar {
        id: bottomBar
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 18
        width: Math.min(920, Math.floor(parent.width * 0.68))
        height: 78
    }

    // ── Right rail — vertical capsule between top and bottom bars ─────────
    RightRail {
        id: rightRail
        anchors {
            top: topBar.bottom
            right: parent.right
            bottom: bottomBar.top
            topMargin: 12
            rightMargin: 16
            bottomMargin: 14
        }
        width: 76
    }

    // ── Image settings panel (floating, draggable) ─────────────────────────
    ImageSettingsPanel {
        id: imgPanel
        x: Math.max(8, rightRail.x - width - 12)
        y: topBar.y + topBar.height + 12
    }

    // Same floating / draggable positioning as ImageSettingsPanel (anchors would block drag)
    SettingsPanel {
        id: settingsPanel
        x: Math.max(8, rightRail.x - width - 12)
        y: topBar.y + topBar.height + 12
        maxPanelHeight: win.height - topBar.y - topBar.height - 12 - bottomBar.height - 36
    }

    // ── Toast notification ─────────────────────────────────────────────────
    Toast {
        id: toast
        z: 200
        anchors {
            horizontalCenter: parent.horizontalCenter
            bottom:           parent.bottom
            bottomMargin:     bottomBar.height + 32
        }
    }

    Connections {
        target: bridge
        function onToastRequested(message) { toast.show(message) }
    }

    // ── Keyboard shortcuts ─────────────────────────────────────────────────
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
