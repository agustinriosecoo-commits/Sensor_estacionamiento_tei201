%% Estado actual del espacio A1: alerta visual "SIN CUPO" / "HAY CUPO"
% MATLAB Visualization para ThingSpeak (TEI201, Grupo 10).
% Lee el campo 1 (ocupado) de las últimas 24 h y muestra un panel de color
% con el estado actual y desde qué hora está así.
% Responde al problema del Avance 1: el conductor sabe si hay cupo antes de llegar.

% ---------- Configuración (completar) ----------
CANAL_ID = 3580318;               % Channel ID (aparece arriba en la página del canal)
READ_KEY = 'XXXXXXXXXXXXXXXX';   % Read API Key (pestaña "API Keys" del canal), o dejar el canal público
ZONA     = 'America/Santiago';
MAX_SILENCIO = minutes(2);        % sin datos por más de esto = sensor desconectado
                                  % (el ESP32 manda un registro cada 30 s)

% ---------- Leer datos ----------
[s, t] = thingSpeakRead(CANAL_ID, 'Fields', 1, 'NumDays', 1, 'ReadKey', READ_KEY);
ok = ~isnan(s);  s = s(ok);  t = t(ok);
if isempty(t.TimeZone), t.TimeZone = 'UTC'; end   % ThingSpeak entrega la hora en UTC
t.TimeZone = ZONA;
ahora = datetime('now', 'TimeZone', ZONA);

% ---------- Decidir qué mostrar ----------
if isempty(s) || ahora - t(end) > MAX_SILENCIO
    color   = [0.55 0.55 0.55];
    titulo  = 'SIN DATOS';
    detalle = 'Sensor desconectado o sin internet';
else
    estado = s(end);
    % Último cambio de estado: el último registro con el estado contrario
    iContrario = find(s ~= estado, 1, 'last');
    if isempty(iContrario)
        desde = t(1);                       % no cambió en las últimas 24 h
    else
        desde = t(iContrario + 1);
    end
    if estado == 1
        color = [0.70 0.21 0.17];  titulo = 'SIN CUPO';
    else
        color = [0.18 0.49 0.31];  titulo = 'HAY CUPO';
    end
    detalle = sprintf('Desde las %s (hace %.0f min)', char(desde, 'HH:mm'), minutes(ahora - desde));
end

% ---------- Dibujar el panel ----------
figure;
axis off;  xlim([0 1]);  ylim([0 1]);  hold on;
rectangle('Position', [0 0 1 1], 'FaceColor', color, 'EdgeColor', 'none', 'Curvature', 0.08);
text(0.5, 0.62, titulo,  'Color', 'w', 'FontSize', 40, 'FontWeight', 'bold', 'HorizontalAlignment', 'center');
text(0.5, 0.30, detalle, 'Color', 'w', 'FontSize', 14, 'HorizontalAlignment', 'center');
title(sprintf('Espacio A1, Alameda (actualizado %s)', char(ahora, 'HH:mm')));
