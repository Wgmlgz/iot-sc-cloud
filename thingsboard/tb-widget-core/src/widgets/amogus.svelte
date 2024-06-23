<script lang="ts">
  import { onMount } from 'svelte';
  import type { WidgetSubscriptionCallbacks } from '../thingsboard-ui-types/src/app/core/api/widget-api.models';
  import type { WidgetContext } from '../thingsboard-ui-types/src/app/modules/home/models/widget-component.models';
  import axios from 'axios';
  import moment from 'moment';

  export let self: WidgetSubscriptionCallbacks & { ctx: WidgetContext };

  let arr: any[] = [];
  const TOOLTIP_TAG = 'rgba(254, 254, 255, 0.76)';
  const CANVAS_TAG = 'rgb(254, 255, 254)';
  const dateRegex =
    /(\w{3} \d{2} \d{4} \d{2}:\d{2}) - (\w{3} \d{2} \d{4} \d{2}:\d{2})/;
  const S3_URL = 'https://iot-sc.storage.yandexcloud.net';
  let canvas: Element | null = null;
  let selected_video: any | null = null;
  $: console.log(canvas);

  onMount(() => {
    canvas = null;
    findCanvas();
  });

  self.onDataUpdated = () => {
    arr = (self.ctx.data ?? []).map(({ data, datasource }, i) => {
      return {
        name: self.ctx.datasources?.[i].name,
        url: data[data.length - 1][1],
        datasource,
      };
    });
  };
  console.log(self);

  const findCanvas = () => {
    const allElements = document.querySelectorAll('*');

    allElements.forEach(element => {
      const style = window.getComputedStyle(element);
      const backgroundColor = style.backgroundColor;
      if (backgroundColor === CANVAS_TAG) {
        canvas = element.querySelector('canvas') ?? null;
        if (!canvas) return;
        canvas.addEventListener('click', onCanvasClick);
      }
    });
    if (!canvas) setTimeout(findCanvas, 100);
  };

  function monthToNumber(month: string) {
    // Convert month name to month number (0-indexed)
    const months: Record<string, number> = {
      Jan: 0,
      Feb: 1,
      Mar: 2,
      Apr: 3,
      May: 4,
      Jun: 5,
      Jul: 6,
      Aug: 7,
      Sep: 8,
      Oct: 9,
      Nov: 10,
      Dec: 11,
    };
    return months[month];
  }

  function parseDateAsUTC(dateStr: string) {
    // Parse a date string formatted as "MMM DD YYYY HH:mm" and treat it as UTC
    const parts = dateStr.match(/(\w{3}) (\d{2}) (\d{4}) (\d{2}):(\d{2})/);
    if (!parts) throw Error('no parts');
    return new Date(
      Date.UTC(
        parseInt(parts[3]),
        monthToNumber(parts[1]),
        parseInt(parts[2]),
        parseInt(parts[4]),
        parseInt(parts[5])
      )
    );
  }

  const onCanvasClick: EventListener = async event => {
    console.log('clicker', event);
    const tooltip = findTooltip();
    console.log(tooltip);
    const elements = tooltip?.querySelectorAll('*') ?? [];
    elements.forEach(async element => {
      const textContent = element.textContent;
      const match = textContent?.match(dateRegex);
      if (match) {
        const startTime = parseDateAsUTC(match[1]);
        const endTime = parseDateAsUTC(match[2]);
        const start = startTime.getTime();
        const end = endTime.getTime();
        console.log(start, end);

        const token = localStorage.getItem('jwt_token');
        const ts = 1719166220 * 1000;
        1719181787229;
        await Promise.all(
          arr.map(async ({ datasource }) => {
            const { data } = await axios.get(
              `/api/plugins/telemetry/${datasource.entityType}/${datasource.entityId}/values/timeseries?keys=video_path&startTs=${start}&endTs=${end}`,
              {
                headers: {
                  'X-Authorization': `Bearer ${token}`,
                },
              }
            );
            console.log(data);
            const t = data?.video_path?.[0];
            if (!t) return;
            selected_video = t;
          })
        );
      }
    });
  };
  const findTooltip = (): Element | null => {
    const allElements = document.querySelectorAll('*');
    let el = null;
    allElements.forEach(element => {
      const style = window.getComputedStyle(element);
      const backgroundColor = style.backgroundColor;
      if (backgroundColor === TOOLTIP_TAG) {
        el = element;
      }
    });
    return el;
  };
</script>

<div class="w-full h-full">
  {#each arr as { url, name }}
    <div>
      <p class="m-y-0">Latest clip from: {name}</p>
      <video class="w-full h-full" controls loop autoplay>
        <track kind="captions" />
        <source src={url} type="video/mp4" />
      </video>
    </div>
  {/each}

  {#if selected_video}
    <div>
      <p class="m-y-0">
        Clip from {moment(selected_video.ts).format('lll')}
      </p>
      {#key selected_video}
        <video class="w-full h-full" controls loop autoplay>
          <track kind="captions" />
          <source src="{S3_URL}/{selected_video.value}" type="video/mp4" />
        </video>
      {/key}
    </div>
  {/if}
</div>
