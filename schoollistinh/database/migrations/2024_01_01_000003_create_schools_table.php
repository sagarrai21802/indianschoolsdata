<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('schools', function (Blueprint $table) {
            $table->id();
            $table->foreignId('city_id')->constrained()->onDelete('cascade');
            $table->foreignId('locality_id')->nullable()->constrained()->onDelete('set null');
            
            // Basic info
            $table->string('name');
            $table->string('slug');
            $table->string('address')->nullable();
            $table->string('locality_name')->nullable();
            
            // Education details
            $table->string('board')->nullable(); // CBSE, ICSE, State Board, etc.
            $table->string('medium')->nullable(); // English, Hindi, etc.
            $table->string('school_type')->nullable(); // Play School, Primary, etc.
            $table->string('established')->nullable();
            $table->string('grades')->nullable();
            
            // Fees
            $table->integer('fees_min')->nullable();
            $table->integer('fees_max')->nullable();
            $table->string('fees_currency')->default('INR');
            $table->text('fees_text')->nullable();
            
            // Contact
            $table->string('phone')->nullable();
            $table->string('email')->nullable();
            $table->string('website')->nullable();
            
            // Ratings
            $table->decimal('rating', 2, 1)->nullable();
            $table->integer('reviews_count')->default(0);
            
            // JSON data storage for flexible fields
            $table->json('json_data')->nullable();
            
            // Images stored as JSON array
            $table->json('images')->nullable();
            
            // Admission status
            $table->string('admission_status')->default('unknown');
            
            // Flags
            $table->boolean('is_active')->default(true);
            $table->boolean('is_featured')->default(false);
            $table->boolean('is_verified')->default(false);
            
            $table->timestamps();
            
            // Indexes
            $table->unique(['city_id', 'slug']);
            $table->index('slug');
            $table->index('board');
            $table->index('school_type');
            $table->index('is_active');
            $table->index('is_featured');
            $table->index('rating');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('schools');
    }
};
