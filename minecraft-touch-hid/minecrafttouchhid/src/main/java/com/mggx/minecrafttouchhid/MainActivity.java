package com.mggx.minecrafttouchhid;

import android.Manifest;
import android.app.Activity;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.SeekBar;
import android.widget.TextView;

import androidx.core.content.ContextCompat;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Set;

public class MainActivity extends Activity {
    private static final int REQ_PERMS = 100;
    private TextView statusView;
    private LinearLayout devicesView;
    private BluetoothAdapter bluetoothAdapter;
    private SharedPreferences prefs;

    private final BroadcastReceiver statusReceiver = new BroadcastReceiver() {
        @Override public void onReceive(Context context, Intent intent) {
            if (HidControllerService.ACTION_STATUS.equals(intent.getAction())) {
                String text = intent.getStringExtra(HidControllerService.EXTRA_STATUS);
                if (text != null) statusView.setText(text);
                refreshDevices();
            }
        }
    };

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences("controls", MODE_PRIVATE);

        BluetoothManager manager = getSystemService(BluetoothManager.class);
        bluetoothAdapter = manager != null ? manager.getAdapter() : null;

        buildUi();
        requestRuntimePermissions();
        startControllerService(HidControllerService.CMD_INIT, null);
    }

    @Override protected void onStart() {
        super.onStart();
        IntentFilter filter = new IntentFilter(HidControllerService.ACTION_STATUS);
        ContextCompat.registerReceiver(
                this,
                statusReceiver,
                filter,
                ContextCompat.RECEIVER_NOT_EXPORTED);
        refreshDevices();
    }

    @Override protected void onStop() {
        try { unregisterReceiver(statusReceiver); } catch (IllegalArgumentException ignored) {}
        super.onStop();
    }

    @Override protected void onResume() {
        super.onResume();
        if (statusView != null) {
            boolean overlay = Settings.canDrawOverlays(this);
            statusView.setText(overlay
                    ? "Overlay permitido. Preparando HID Bluetooth…"
                    : "Falta permiso para mostrar controles sobre Moonlight.");
        }
        refreshDevices();
    }

    private void buildUi() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.rgb(12, 14, 18));

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(20), dp(20), dp(20), dp(32));
        scroll.addView(root, new ScrollView.LayoutParams(
                ScrollView.LayoutParams.MATCH_PARENT,
                ScrollView.LayoutParams.WRAP_CONTENT));

        TextView title = text("MGGX Minecraft Touch", 28, true);
        root.addView(title);
        TextView subtitle = text("Joystick + teclado + mouse Bluetooth para jugar Minecraft Java mientras usás Moonlight.", 15, false);
        subtitle.setTextColor(Color.rgb(190, 196, 205));
        root.addView(subtitle, lpTop(8));

        statusView = text("Iniciando…", 16, true);
        statusView.setPadding(dp(14), dp(12), dp(14), dp(12));
        statusView.setBackgroundColor(Color.rgb(30, 35, 44));
        root.addView(statusView, lpTop(18));

        Button overlayPermission = button("1. Permitir controles sobre otras apps");
        overlayPermission.setOnClickListener(v -> {
            Intent intent = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:" + getPackageName()));
            startActivity(intent);
        });
        root.addView(overlayPermission, lpTop(16));

        Button discoverable = button("2. Hacer visible el celular por Bluetooth (120 s)");
        discoverable.setOnClickListener(v -> requestDiscoverable());
        root.addView(discoverable, lpTop(10));

        Button bluetoothSettings = button("Abrir ajustes Bluetooth");
        bluetoothSettings.setOnClickListener(v -> startActivity(new Intent(Settings.ACTION_BLUETOOTH_SETTINGS)));
        root.addView(bluetoothSettings, lpTop(10));

        TextView pairHelp = text("En Windows: Configuración → Bluetooth y dispositivos → Agregar dispositivo. Emparejá este celular una vez. Después elegí tu PC abajo.", 14, false);
        pairHelp.setTextColor(Color.rgb(174, 180, 190));
        root.addView(pairHelp, lpTop(12));

        TextView devicesTitle = text("PCs/dispositivos emparejados", 18, true);
        root.addView(devicesTitle, lpTop(22));

        devicesView = new LinearLayout(this);
        devicesView.setOrientation(LinearLayout.VERTICAL);
        root.addView(devicesView, lpTop(6));

        Button refresh = button("Actualizar dispositivos");
        refresh.setOnClickListener(v -> refreshDevices());
        root.addView(refresh, lpTop(8));

        TextView sensitivityLabel = text("Sensibilidad de cámara", 16, true);
        root.addView(sensitivityLabel, lpTop(24));
        SeekBar sensitivity = new SeekBar(this);
        sensitivity.setMax(230);
        int sensitivityProgress = Math.max(0, Math.min(230,
                Math.round((prefs.getFloat("sensitivity", 1.0f) - 0.2f) * 100f)));
        sensitivity.setProgress(sensitivityProgress);
        sensitivity.setOnSeekBarChangeListener(new SimpleSeekListener() {
            @Override public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                prefs.edit().putFloat("sensitivity", 0.2f + progress / 100f).apply();
            }
        });
        root.addView(sensitivity);

        TextView opacityLabel = text("Opacidad de los controles", 16, true);
        root.addView(opacityLabel, lpTop(10));
        SeekBar opacity = new SeekBar(this);
        opacity.setMax(190);
        opacity.setProgress(Math.max(0, Math.min(190, prefs.getInt("opacity", 105) - 40)));
        opacity.setOnSeekBarChangeListener(new SimpleSeekListener() {
            @Override public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                prefs.edit().putInt("opacity", 40 + progress).apply();
            }
        });
        root.addView(opacity);

        CheckBox invertY = new CheckBox(this);
        invertY.setText("Invertir eje Y de la cámara");
        invertY.setTextColor(Color.WHITE);
        invertY.setChecked(prefs.getBoolean("invert_y", false));
        invertY.setOnCheckedChangeListener((buttonView, isChecked) ->
                prefs.edit().putBoolean("invert_y", isChecked).apply());
        root.addView(invertY, lpTop(8));

        Button showOverlay = button("▶ Mostrar controles y abrir Moonlight");
        showOverlay.setOnClickListener(v -> {
            if (!Settings.canDrawOverlays(this)) {
                statusView.setText("Primero concedé el permiso de overlay.");
                return;
            }
            startControllerService(HidControllerService.CMD_SHOW_OVERLAY, null);
            Intent launch = getPackageManager().getLaunchIntentForPackage("com.limelight");
            if (launch != null) startActivity(launch);
            else statusView.setText("Controles activos. Abrí Moonlight manualmente.");
        });
        root.addView(showOverlay, lpTop(22));

        Button hideOverlay = button("Cerrar controles flotantes");
        hideOverlay.setOnClickListener(v -> startControllerService(HidControllerService.CMD_HIDE_OVERLAY, null));
        root.addView(hideOverlay, lpTop(10));

        TextView legend = text("Controles: joystick=WASD · zona derecha=mouse · ATK=click izq. · USE=click der. · JUMP=Space · SNEAK=Shift · SPRINT=Ctrl · INV=E · Q · ESC · F3 · hotbar 1–9. Pastilla flotante 🎮 CONTROLES / 👆 TOUCH: cambia al instante entre controles HID y touch nativo de Moonlight. El botón TOUCH del overlay hace lo mismo.", 14, false);
        legend.setTextColor(Color.rgb(174, 180, 190));
        legend.setGravity(Gravity.START);
        root.addView(legend, lpTop(18));

        setContentView(scroll);
    }

    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQ_PERMS) {
            startControllerService(HidControllerService.CMD_INIT, null);
            refreshDevices();
        }
    }

    private void requestRuntimePermissions() {
        List<String> wanted = new ArrayList<>();
        if (Build.VERSION.SDK_INT >= 31) {
            if (checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED)
                wanted.add(Manifest.permission.BLUETOOTH_CONNECT);
            if (checkSelfPermission(Manifest.permission.BLUETOOTH_ADVERTISE) != PackageManager.PERMISSION_GRANTED)
                wanted.add(Manifest.permission.BLUETOOTH_ADVERTISE);
        }
        if (Build.VERSION.SDK_INT >= 33 &&
                checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            wanted.add(Manifest.permission.POST_NOTIFICATIONS);
        }
        if (!wanted.isEmpty()) requestPermissions(wanted.toArray(new String[0]), REQ_PERMS);
    }

    private boolean hasBluetoothConnectPermission() {
        return Build.VERSION.SDK_INT < 31 ||
                checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED;
    }

    private void requestDiscoverable() {
        if (bluetoothAdapter == null) {
            statusView.setText("Este dispositivo no tiene Bluetooth disponible.");
            return;
        }
        if (Build.VERSION.SDK_INT >= 31 &&
                checkSelfPermission(Manifest.permission.BLUETOOTH_ADVERTISE) != PackageManager.PERMISSION_GRANTED) {
            requestRuntimePermissions();
            return;
        }
        Intent discoverable = new Intent(BluetoothAdapter.ACTION_REQUEST_DISCOVERABLE);
        discoverable.putExtra(BluetoothAdapter.EXTRA_DISCOVERABLE_DURATION, 120);
        startActivity(discoverable);
    }

    private void refreshDevices() {
        if (devicesView == null) return;
        devicesView.removeAllViews();
        if (bluetoothAdapter == null) {
            devicesView.addView(text("Bluetooth no disponible.", 14, false));
            return;
        }
        if (!hasBluetoothConnectPermission()) {
            devicesView.addView(text("Falta permiso Bluetooth.", 14, false));
            return;
        }

        Set<BluetoothDevice> bonded;
        try { bonded = bluetoothAdapter.getBondedDevices(); }
        catch (SecurityException e) {
            devicesView.addView(text("Android bloqueó el acceso Bluetooth. Revisá permisos.", 14, false));
            return;
        }

        if (bonded == null || bonded.isEmpty()) {
            devicesView.addView(text("Todavía no hay dispositivos emparejados.", 14, false));
            return;
        }

        List<BluetoothDevice> devices = new ArrayList<>(bonded);
        devices.sort(Comparator.comparing(d -> safeName(d).toLowerCase()));
        for (BluetoothDevice device : devices) {
            String name = safeName(device);
            Button b = button("Conectar: " + name + "\n" + device.getAddress());
            b.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
            b.setOnClickListener(v -> startControllerService(HidControllerService.CMD_CONNECT, device.getAddress()));
            devicesView.addView(b, lpTop(8));
        }
    }

    private String safeName(BluetoothDevice device) {
        try {
            String n = device.getName();
            return n == null || n.trim().isEmpty() ? "Dispositivo Bluetooth" : n;
        } catch (SecurityException e) {
            return "Dispositivo Bluetooth";
        }
    }

    private void startControllerService(String command, String address) {
        Intent intent = new Intent(this, HidControllerService.class).setAction(command);
        if (address != null) intent.putExtra(HidControllerService.EXTRA_ADDRESS, address);
        if (Build.VERSION.SDK_INT >= 26) startForegroundService(intent);
        else startService(intent);
    }

    private TextView text(String value, int sp, boolean bold) {
        TextView tv = new TextView(this);
        tv.setText(value);
        tv.setTextSize(sp);
        tv.setTextColor(Color.WHITE);
        if (bold) tv.setTypeface(tv.getTypeface(), android.graphics.Typeface.BOLD);
        return tv;
    }

    private Button button(String value) {
        Button b = new Button(this);
        b.setText(value);
        b.setAllCaps(false);
        b.setTextSize(15);
        return b;
    }

    private LinearLayout.LayoutParams lpTop(int topDp) {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
        p.topMargin = dp(topDp);
        return p;
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }

    private abstract static class SimpleSeekListener implements SeekBar.OnSeekBarChangeListener {
        @Override public void onStartTrackingTouch(SeekBar seekBar) {}
        @Override public void onStopTrackingTouch(SeekBar seekBar) {}
    }
}
