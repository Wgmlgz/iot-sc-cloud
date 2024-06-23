import { defineConfig, Plugin } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import fs from 'fs';
import path from 'path';
import axios from 'axios';
import UnoCSS from 'unocss/vite'

// try use it its jwt  lol TODO move to .env
const TOKEN =
  'Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ0ZW5hbnRAdGhpbmdzYm9hcmQub3JnIiwidXNlcklkIjoiOGU5YWU0YjAtMTlkYy0xMWVmLThmZDYtNmJhNGFjMTdiM2YzIiwic2NvcGVzIjpbIlRFTkFOVF9BRE1JTiJdLCJzZXNzaW9uSWQiOiJiOTg0NmJhYi04ZWYyLTQ0ZjctYTI4ZS1hYzBmYjJmYmVjODciLCJpc3MiOiJ0aGluZ3Nib2FyZC5pbyIsImlhdCI6MTcxOTE4MTI5MiwiZXhwIjoxNzE5MTkwMjkyLCJlbmFibGVkIjp0cnVlLCJpc1B1YmxpYyI6ZmFsc2UsInRlbmFudElkIjoiOGRiYTZmYzAtMTlkYy0xMWVmLThmZDYtNmJhNGFjMTdiM2YzIiwiY3VzdG9tZXJJZCI6IjEzODE0MDAwLTFkZDItMTFiMi04MDgwLTgwODA4MDgwODA4MCJ9.01BwMuNGl5CLvifGIdp0mu2pTEgLP-Y-Ghgrvv-zFjlV_Pakqv4DrRaNQ3n3kDVEkUZPm120T2mrl4_7oCnH1A';

const TB_URL = 'http://158.160.155.134:8080';
//  '/api/widgetType/{widgetTypeId}{?inlineImages}'

type WidgetEntryPluginOptions = {
  widgetsDir: string;
  outputDir: string;
  initTemplatePath: string;
};
const WidgetEntryPlugin = (options: WidgetEntryPluginOptions): Plugin => {
  const out_paths: { configFilePath: string; jsFilePath: string }[] = [];

  const {
    widgetsDir = 'src/widgets',
    outputDir = 'src/entries',
    initTemplatePath = 'src/initTemplate.js',
  } = options;

  async function uploadBuildFiles(options: WidgetEntryPluginOptions) {
    // Example function to handle file upload logic to ThingsBoard
    console.log('Uploading build files to ThingsBoard...');

    await Promise.all(
      out_paths.map(async ({ configFilePath, jsFilePath }) => {
        try {
          const js = fs.readFileSync(jsFilePath, 'utf8');

          const obj = JSON.parse(fs.readFileSync(configFilePath, 'utf8'));

          const { widgetTypeId, extraDescriptor } = obj;
          const { data } = await axios.get(
            `${TB_URL}/api/widgetType/${widgetTypeId}`,
            {
              headers: {
                'X-Authorization': TOKEN,
              },
            }
          );

          data.descriptor.controllerScript = js;
          data.descriptor = {
            ...data.descriptor,
            ...extraDescriptor,
          };
          const res = await axios.post(
            `${TB_URL}/api/widgetType?updateExistingByFqn=true`,
            data,
            {
              headers: {
                'X-Authorization': TOKEN,
              },
            }
          );
        } catch (e) {
          console.error(e);
        }
      })
    );
    // Logic to upload files to ThingsBoard would go here
  }

  return {
    name: 'vite-plugin-widget-entry',
    configResolved(config) {
      // Ensure the output directory exists
      if (!fs.existsSync(path.resolve(config.root, outputDir))) {
        fs.mkdirSync(path.resolve(config.root, outputDir));
      }

      // Read the template file
      const template = fs.readFileSync(
        path.resolve(config.root, initTemplatePath),
        'utf8'
      );

      // Generate an entry file for each widget
      fs.readdirSync(path.resolve(config.root, widgetsDir))
        .filter(file => file.endsWith('.svelte'))
        .forEach(file => {
          const widgetName = file.replace(/\.svelte$/, '');
          const entryContent = template.replace(/__WIDGET__/g, widgetName);
          const entryFilePath = path.resolve(
            config.root,
            outputDir,
            `${widgetName}.ts`
          );
          const configFilePath = path.resolve(
            config.root,
            outputDir,
            `${widgetName}.json`
          );
          const jsFilePath = path.resolve(
            config.root,
            'dist',
            `${widgetName}.js`
          );
          fs.writeFileSync(entryFilePath, entryContent);
          out_paths.push({ jsFilePath, configFilePath });
        });

      console.log('Widget entry points generated.');
    },
    async writeBundle() {
      console.log('Build is complete, executing post-build tasks...');
      // Here you can execute any code or function call you need.
      // For example, uploading files to a server:
      await uploadBuildFiles(options);
    },
  };
};

export default defineConfig({
  plugins: [
    UnoCSS(),
    svelte(),
    WidgetEntryPlugin({
      widgetsDir: 'src/widgets',
      outputDir: 'src/entries',
      initTemplatePath: 'src/initTemplate.js',
    }),
  ],
  build: {
    // minify: false,
    rollupOptions: {
      // Dynamically set input based on generated entry files
      input: (() => {
        const entriesDir = path.resolve(__dirname, 'src', 'entries');
        return fs.readdirSync(entriesDir).reduce((entries: any, file) => {
          if (file.endsWith('.ts')) {
            const name = file.replace(/\.ts$/, '');
            entries[name] = path.resolve(entriesDir, file);
          }
          return entries;
        }, {});
      })(),
      output: {
        format: 'iife', // Immediate Invoked Function Expression
        dir: 'dist',
        entryFileNames: `[name].js`,
      },
    },
  },
});
