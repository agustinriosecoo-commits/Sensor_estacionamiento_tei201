%% Porcentaje de ocupación por hora (últimas 24 h)
% MATLAB Visualization para ThingSpeak (TEI201, Grupo 10).
% Reconstruye el estado minuto a minuto a partir de los registros (cambios + periódicos)
% y calcula qué % de cada hora estuvo ocupado el espacio.
% Sirve para ver las horas peak: cuándo es más difícil encontrar estacionamiento.

% ---------- Configuración (completar) ----------
CANAL_ID = 3580318;
READ_KEY = 'XXXXXXXXXXXXXXXX';   % Read API Key del canal (o canal público)
ZONA     = 'America/Santiago';
MAX_SILENCIO = minutes(2);   % si pasan más de 2 min sin registros, ese tiempo no se cuenta

% ---------- Leer datos ----------
[s, t] = thingSpeakRead(CANAL_ID, 'Fields', 1, 'NumDays', 1, 'ReadKey', READ_KEY);
ok = ~isnan(s);  s = s(ok);  t = t(ok);
if isempty(t.TimeZone), t.TimeZone = 'UTC'; end
t.TimeZone = ZONA;
[t, iu] = unique(t);  s = s(iu);              % orden por hora y sin repetidos
ahora = datetime('now', 'TimeZone', ZONA);

figure;
if numel(s) < 2
    axis off;
    text(0.5, 0.5, 'Aún no hay datos suficientes', 'FontSize', 16, 'HorizontalAlignment', 'center');
    return
end

% ---------- Estado minuto a minuto ----------
% Entre dos registros, el estado es el del registro anterior.
bordes = [t; max(ahora, t(end) + seconds(1))];
grilla = (dateshift(t(1), 'end', 'minute') : minutes(1) : ahora)';
idx = discretize(grilla, bordes);              % a qué tramo pertenece cada minuto
v = ~isnan(idx);  grilla = grilla(v);  idx = idx(v);
estado = s(idx);
estado(grilla - t(idx) > MAX_SILENCIO) = NaN;  % sensor apagado: sin información

% ---------- % ocupado por hora (siempre las 24 horas, aunque no haya datos) ----------
horas = dateshift(ahora, 'start', 'hour') - hours(23:-1:0)';   % las últimas 24 horas
horaDeCadaMinuto = dateshift(grilla, 'start', 'hour');
pct = NaN(24, 1);
for h = 1:24
    enEstaHora = horaDeCadaMinuto == horas(h);
    if any(enEstaHora)
        pct(h) = 100 * mean(estado(enEstaHora), 'omitnan');
    end
end

% ---------- Gráfico ----------
% Eje x por posición (1 a 24) para que cada barra mida exactamente una hora
bar(1:24, pct, 0.8, 'FaceColor', [0.70 0.21 0.17]);
xlim([0.5 24.5]);
ylim([0 100]);
ylabel('% del tiempo ocupado');
xlabel('Hora');
xticks(1:3:24);
xticklabels(cellstr(char(horas(1:3:24), 'HH:00')));
grid on;
title(sprintf('Ocupación por hora, últimas 24 h (promedio %.0f %%)', 100 * mean(estado, 'omitnan')));
