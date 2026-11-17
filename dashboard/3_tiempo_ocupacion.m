%% Tiempo de ocupación: duración de cada estacionamiento y promedio (últimas 24 h)
% MATLAB Visualization para ThingSpeak (TEI201, Grupo 10).
% Una "ocupación" va desde que el campo 1 pasa de 0 a 1 hasta que vuelve a 0.
% Como el ESP32 registra cada cambio con su hora exacta, la duración es precisa.
% Sirve para estimar la rotación del espacio: cuánto tarda en liberarse.

% ---------- Configuración (completar) ----------
CANAL_ID = 3580318;
READ_KEY = 'XXXXXXXXXXXXXXXX';   % Read API Key del canal (o canal público)
ZONA     = 'America/Santiago';
MAX_BARRAS = 20;             % en el gráfico se muestran las últimas 20 ocupaciones

% ---------- Leer datos ----------
[s, t] = thingSpeakRead(CANAL_ID, 'Fields', 1, 'NumDays', 1, 'ReadKey', READ_KEY);
ok = ~isnan(s);  s = s(ok);  t = t(ok);
if isempty(t.TimeZone), t.TimeZone = 'UTC'; end
t.TimeZone = ZONA;
[t, iu] = unique(t);  s = s(iu);

% ---------- Detectar ocupaciones completas ----------
d = diff(s);
inicios = find(d ==  1) + 1;     % primer registro "ocupado" de cada ocupación
fines   = find(d == -1) + 1;     % primer registro "libre" después de una ocupación

durMin = zeros(0, 1);            % duración de cada ocupación, en minutos
tIni   = t([]);                  % hora de inicio de cada ocupación
for i = 1:numel(inicios)
    f = fines(find(fines > inicios(i), 1));
    if ~isempty(f)               % solo ocupaciones que ya terminaron
        durMin(end+1, 1) = minutes(t(f) - t(inicios(i)));
        tIni(end+1, 1)   = t(inicios(i));
    end
end

% ---------- Gráfico ----------
figure;
if isempty(durMin)
    axis off;
    text(0.5, 0.5, 'Sin ocupaciones completas en las últimas 24 h', ...
         'FontSize', 14, 'HorizontalAlignment', 'center');
    return
end

promedio = mean(durMin);
if promedio < 1
    txtProm = sprintf('%.0f s', promedio * 60);
else
    txtProm = sprintf('%.1f min', promedio);
end

n  = numel(durMin);
k  = max(1, n - MAX_BARRAS + 1) : n;             % últimas ocupaciones
bar(1:numel(k), durMin(k), 'FaceColor', [0.18 0.40 0.60]);
hold on;
yline(promedio, '--', ['Promedio: ' txtProm], 'LineWidth', 1.5);
xticks(1:numel(k));
xticklabels(cellstr(char(tIni(k), 'HH:mm')));
xlabel('Hora de llegada');
ylabel('Duración (minutos)');
grid on;
title(sprintf('Tiempo de ocupación, últimas 24 h: %d ocupaciones, promedio %s', n, txtProm));
