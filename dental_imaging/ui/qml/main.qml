import QtQuick
import QtQuick.Controls

// Root item — full-bleed camera preview with chrome overlaid at edges.
// "bridge" and "appName"/"appSubName" are set as context properties from Python.
Item {
    id: root
    focus: true

    // ── Live camera preview (full-bleed, behind all chrome) ───────────────
    Image {
        id:       cameraView
        anchors.fill: parent
        // QQuickImageProvider registered as "camera" in Python
        source:   "image://camera/frame?" + bridge.frameCounter
        cache:    false
        fillMode: Image.PreserveAspectFit
        smooth:   true
        asynchronous: false

        // Placeholder before first frame
        Rectangle {
            anchors.fill: parent
            color:        "#101214"
            visible:      cameraView.status !== Image.Ready
            Text {
                anchors.centerIn: parent
                text:             "Waiting for camera…"
                color:            "#505060"
                font.pixelSize:   18
            }
        }
    }

    // ── Top bar ───────────────────────────────────────────────────────────
    TopBar {
        id:      topBar
        anchors { top: parent.top; left: parent.left; right: rightRail.left }
        height:  62
    }

    // ── Right rail ────────────────────────────────────────────────────────
    RightRail {
        id:      rightRail
        anchors { top: parent.top; right: parent.right; bottom: parent.bottom }
        width:   92
    }

    // ── Bottom bar ────────────────────────────────────────────────────────
    BottomBar {
        id:      bottomBar
        anchors { left: parent.left; right: rightRail.left; bottom: parent.bottom }
        height:  100
    }

    // ── Floating image settings panel ─────────────────────────────────────
    ImageSettingsPanel {
        id: imagePanel
        // Position: left of rail, below top bar, with margin
        x: rightRail.x - width - 14
        y: topBar.height + 14

        // Clamp so it never goes off-screen
        onYChanged: {
            if (y + height > bottomBar.y - 14)
                y = bottomBar.y - height - 14
        }

        // Drag support
        MouseArea {
            anchors.fill:    parent
            drag.target:     parent
            drag.minimumX:   0
            drag.maximumX:   rightRail.x - parent.width - 4
            drag.minimumY:   topBar.height
            drag.maximumY:   bottomBar.y - parent.height
            cursorShape:     Qt.SizeAllCursor
            // Don't block slider interactions — only drag on title area
            drag.axis:       Drag.XAndYAxis
            // Only drag from the header (top 44 px)
            enabled:         mouseY < 44
        }
    }

    // ── Toast overlay ─────────────────────────────────────────────────────
    Toast {
        id: toast
        anchors {
            horizontalCenter: parent.horizontalCenter
            bottom:           bottomBar.top
            bottomMargin:     18
        }
        z: 100
    }

    // ── Bridge → Toast connection ──────────────────────────────────────────
    Connections {
        target: bridge
        function onToastRequested(message) { toast.show(message) }
    }

    // ── Key shortcuts ─────────────────────────────────────────────────────
    Keys.onPressed: (event) => {
        if (event.key === Qt.Key_Space) { bridge.onCapture(); event.accepted = true }
    }
}
