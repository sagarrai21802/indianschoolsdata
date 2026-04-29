<?php

namespace App\Filament\Resources;

use App\Filament\Resources\SchoolResource\Pages;
use App\Models\School;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;

class SchoolResource extends Resource
{
    protected static ?string $model = School::class;
    protected static ?string $navigationIcon = 'heroicon-o-academic-cap';
    protected static ?string $navigationGroup = 'School Management';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Select::make('city_id')
                    ->relationship('city', 'name')
                    ->required()
                    ->searchable(),
                
                Forms\Components\Select::make('locality_id')
                    ->relationship('locality', 'name')
                    ->searchable(),
                
                Forms\Components\TextInput::make('name')
                    ->required()
                    ->maxLength(255),
                
                Forms\Components\TextInput::make('slug')
                    ->required()
                    ->maxLength(255)
                    ->unique(ignoreRecord: true),
                
                Forms\Components\Textarea::make('address')
                    ->maxLength(65535)
                    ->columnSpanFull(),
                
                Forms\Components\TextInput::make('locality_name')
                    ->maxLength(255),
                
                Forms\Components\TextInput::make('board')
                    ->maxLength(255),
                
                Forms\Components\TextInput::make('medium')
                    ->maxLength(255),
                
                Forms\Components\TextInput::make('school_type')
                    ->maxLength(255),
                
                Forms\Components\TextInput::make('established')
                    ->maxLength(255),
                
                Forms\Components\TextInput::make('grades')
                    ->maxLength(255),
                
                Forms\Components\Section::make('Fees')
                    ->schema([
                        Forms\Components\TextInput::make('fees_min')
                            ->numeric()
                            ->prefix('₹'),
                        Forms\Components\TextInput::make('fees_max')
                            ->numeric()
                            ->prefix('₹'),
                        Forms\Components\TextInput::make('fees_currency')
                            ->default('INR'),
                    ])->columns(3),
                
                Forms\Components\Section::make('Contact')
                    ->schema([
                        Forms\Components\TextInput::make('phone')
                            ->tel()
                            ->maxLength(255),
                        Forms\Components\TextInput::make('email')
                            ->email()
                            ->maxLength(255),
                        Forms\Components\TextInput::make('website')
                            ->url()
                            ->maxLength(255),
                    ])->columns(3),
                
                Forms\Components\Section::make('Ratings')
                    ->schema([
                        Forms\Components\TextInput::make('rating')
                            ->numeric()
                            ->step(0.1)
                            ->minValue(0)
                            ->maxValue(5),
                        Forms\Components\TextInput::make('reviews_count')
                            ->numeric()
                            ->integer(),
                    ])->columns(2),
                
                Forms\Components\Select::make('facilities')
                    ->relationship('facilities', 'name')
                    ->multiple()
                    ->preload()
                    ->searchable(),
                
                Forms\Components\Toggle::make('is_active')
                    ->default(true),
                Forms\Components\Toggle::make('is_featured')
                    ->default(false),
                Forms\Components\Toggle::make('is_verified')
                    ->default(false),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('name')
                    ->searchable()
                    ->sortable(),
                Tables\Columns\TextColumn::make('city.name')
                    ->sortable(),
                Tables\Columns\TextColumn::make('locality.name')
                    ->sortable(),
                Tables\Columns\TextColumn::make('board')
                    ->searchable()
                    ->sortable(),
                Tables\Columns\TextColumn::make('school_type')
                    ->searchable(),
                Tables\Columns\TextColumn::make('rating')
                    ->numeric()
                    ->sortable(),
                Tables\Columns\IconColumn::make('is_active')
                    ->boolean(),
                Tables\Columns\IconColumn::make('is_featured')
                    ->boolean(),
                Tables\Columns\TextColumn::make('created_at')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->filters([
                Tables\Filters\SelectFilter::make('city')
                    ->relationship('city', 'name'),
                Tables\Filters\SelectFilter::make('board')
                    ->options(fn () => School::distinct()->pluck('board', 'board')->filter()->toArray()),
                Tables\Filters\TernaryFilter::make('is_active'),
                Tables\Filters\TernaryFilter::make('is_featured'),
            ])
            ->actions([
                Tables\Actions\EditAction::make(),
                Tables\Actions\DeleteAction::make(),
            ])
            ->bulkActions([
                Tables\Actions\BulkActionGroup::make([
                    Tables\Actions\DeleteBulkAction::make(),
                ]),
            ])
            ->defaultSort('created_at', 'desc');
    }

    public static function getRelations(): array
    {
        return [
            //
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListSchools::route('/'),
            'create' => Pages\CreateSchool::route('/create'),
            'edit' => Pages\EditSchool::route('/{record}/edit'),
        ];
    }
}
