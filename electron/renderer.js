// This file is required by the index.html file and will
// be executed in the renderer process for that window.
// No Node.js APIs are available in this process because
// `nodeIntegration` is turned off. Use `preload.js` to
// selectively enable features needed in the rendering
// process.

// Adapted from https://www.electronjs.org/docs/latest/tutorial/devices
async function testIt() {
  const device = await navigator.bluetooth.requestDevice({
    acceptAllDevices: true
  })
  document.getElementById('device-name').innerHTML = device.name || `ID: ${device.id}`
}

document.getElementById('clickme').addEventListener('click',testIt)

window.electronAPI.bluetoothPairingRequest((event, details) => {
  const response = {}
  
  switch (details.pairingKind) {
    case 'confirm': {
      response.confirmed = confirm(`Do you want to connect to device ${details.deviceId}?`)
      break
    }
    case 'confirmPin': {
      response.confirmed = confirm(`Does the pin ${details.pin} match the pin displayed on device ${details.deviceId}?`)
      break
    }
    case 'providePin': {
      const pin = prompt(`Please provide a pin for ${details.deviceId}.`)
      if (pin) {
        response.pin = pin
        response.confirmed = true
      } else {
        response.confirmed = false
      }
    }
  }

  window.electronAPI.bluetoothPairingResponse(response)
})