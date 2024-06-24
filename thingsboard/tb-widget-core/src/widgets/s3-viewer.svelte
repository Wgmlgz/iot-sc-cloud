<script lang="ts">
  import prettyBytes from 'pretty-bytes';

  import { Button, DataTable } from 'carbon-components-svelte';

  import type { WidgetSubscriptionCallbacks } from '../thingsboard-ui-types/src/app/core/api/widget-api.models';
  import type { WidgetContext } from '../thingsboard-ui-types/src/app/modules/home/models/widget-component.models';
  import 'carbon-components-svelte/css/white.css';
  import moment from 'moment';

  export let self: WidgetSubscriptionCallbacks & { ctx: WidgetContext };

  let arr: any[] = [];
  const S3_URL = 'https://iot-sc.storage.yandexcloud.net';

  self.onDataUpdated = () => {
    arr = (self.ctx.data ?? []).map(({ data, datasource }, i) => {
      currentPrefix = 'device-videos/' + datasource.entityId + '/';
      listObjects(currentPrefix);

      return {
        datasource,
      };
    });
  };

  console.log('amogus', self);

  let files: any[] = [];
  let currentPrefix = 'device-videos/';
  let prefixStack: string[] = [];

  async function listObjects(prefix: string) {
    const url = `${S3_URL}/?prefix=${encodeURIComponent(prefix)}&delimiter=/`;
    try {
      const response = await fetch(url);
      const text = await response.text();
      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(text, 'application/xml');

      files = [];
      const commonPrefixes = xmlDoc.getElementsByTagName('CommonPrefixes');
      for (let i = 0; i < commonPrefixes.length; i++) {
        const Prefix =
          commonPrefixes[i].getElementsByTagName('Prefix')[0].childNodes[0]
            .nodeValue;

        const Name = Prefix?.replace(/\/$/, '').split('/').pop();
        files.push({
          id: Prefix,
          Name,
          Prefix,
          Key: Prefix,
          LastModified: '-',
          Size: '-',
        });
      }

      const contents = xmlDoc.getElementsByTagName('Contents');
      for (let i = 0; i < contents.length; i++) {
        const key =
          contents[i].getElementsByTagName('Key')[0].childNodes[0].nodeValue;
        const lastModified =
          contents[i].getElementsByTagName('LastModified')[0].childNodes[0]
            .nodeValue;
        const size =
          contents[i].getElementsByTagName('Size')[0].childNodes[0].nodeValue;
        const Name = key?.replace(/\/$/, '').split('/').pop();

        files.push({
          id: key,
          Name,
          Key: key,
          LastModified: moment(lastModified).format('lll') ?? '-',
          Size: prettyBytes(Number(size || '0')) ?? '-',
        });
      }
      files = files;
    } catch (err) {
      console.error('Error fetching from S3', err);
    }
  }

  async function openFile(key: string) {
    const url = `${S3_URL}/${encodeURIComponent(key)}`;

    try {
      const response = await fetch(url);
      const blob = new Blob([await response.blob()], { type: 'video/mp4' }); // Get a Blob from the response
      const blobUrl = URL.createObjectURL(blob); // Create a URL for the Blob
      window.open(blobUrl, '_blank'); // Open the blob URL in a new tab
    } catch (err) {
      console.error('Error fetching file', err);
    }
  }

  function navigateTo(prefix: string) {
    prefixStack = [...prefixStack, currentPrefix];
    currentPrefix = prefix;
    listObjects(currentPrefix);
  }

  function goUp() {
    if (prefixStack.length > 0) {
      currentPrefix = prefixStack.pop() ?? '';
      prefixStack = prefixStack;
      listObjects(currentPrefix);
    }
  }
</script>

<div class="w-full h-full">
  {#each arr as { datasource }}
    <div>
      <p class="m-y-0">Browsing: {datasource.entityName}</p>
    </div>
  {/each}

  <Button
    kind="ghost"
    size="small"
    on:click={goUp}
    disabled={prefixStack.length === 0}>Go Up</Button
  >

  <DataTable
    headers={[
      { key: 'Key', value: 'Name' },
      { key: 'Size', value: 'Size' },
      { key: 'LastModified', value: 'Last Modified' },
    ]}
    rows={files}
  >
    <svelte:fragment slot="cell" let:row let:cell>
      {#if cell.key === 'Key' && !row.Prefix}
        <Button kind="ghost" on:click={() => openFile(row.Key)} size="small">
          {row.Name}
        </Button>
      {:else if cell.key === 'Key' && row.Prefix}
        <!-- else if content here -->
        <Button
          kind="ghost"
          on:click={() => navigateTo(row.Prefix)}
          size="small"
        >
          {row.Name}
        </Button>
      {:else}
        {cell.value}
      {/if}
    </svelte:fragment>
  </DataTable>
</div>
