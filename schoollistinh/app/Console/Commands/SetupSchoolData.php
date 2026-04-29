<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Illuminate\Support\Facades\File;

class SetupSchoolData extends Command
{
    protected $signature = 'schools:setup';
    protected $description = 'Copy scraped_data to storage/app/schools';

    public function handle(): int
    {
        $sourcePath = base_path('../scraped_data');
        $targetPath = storage_path('app/schools');

        if (!File::isDirectory($sourcePath)) {
            $this->error("Source directory not found: {$sourcePath}");
            return Command::FAILURE;
        }

        // Create target directory
        if (!File::isDirectory($targetPath)) {
            File::makeDirectory($targetPath, 0755, true);
        }

        $this->info('Copying school data...');

        // Copy all city directories
        foreach (File::directories($sourcePath) as $cityDir) {
            $cityName = basename($cityDir);
            
            // Skip hidden/system directories
            if (str_starts_with($cityName, '.') || str_starts_with($cityName, '_')) {
                continue;
            }

            $targetCityDir = $targetPath . '/' . $cityName;
            
            if (!File::isDirectory($targetCityDir)) {
                File::makeDirectory($targetCityDir, 0755, true);
            }

            // Copy _city.json
            $cityJson = $cityDir . '/_city.json';
            if (File::exists($cityJson)) {
                File::copy($cityJson, $targetCityDir . '/_city.json');
            }

            // Copy school directories
            foreach (File::directories($cityDir) as $schoolDir) {
                $schoolName = basename($schoolDir);
                
                if (str_starts_with($schoolName, '.') || str_starts_with($schoolName, '_')) {
                    continue;
                }

                $targetSchoolDir = $targetCityDir . '/' . $schoolName;
                
                if (!File::isDirectory($targetSchoolDir)) {
                    File::makeDirectory($targetSchoolDir, 0755, true);
                }

                // Copy about.json
                $aboutJson = $schoolDir . '/about.json';
                if (File::exists($aboutJson)) {
                    File::copy($aboutJson, $targetSchoolDir . '/about.json');
                }
            }
        }

        $this->info('School data setup complete!');
        $this->info("Data copied to: {$targetPath}");

        return Command::SUCCESS;
    }
}
