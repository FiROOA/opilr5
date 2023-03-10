import sys
from time import sleep

import pygame

from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button
from ship import Ship
from bullet import Bullet
from alien import Alien


class AlienInvasion:
    """Загальний клас для керування ігровими даними та поведінкою"""

    def __init__(self):
        """Ініціалізація гри та виділення ресурсів"""
        pygame.init()
        self.settings = Settings()

        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height
        pygame.display.set_caption("Alien Invasion")

        # Створення зберігання статистики гри та табло
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()

        self._create_fleet()

        # Кнопка Play
        self.play_button = Button(self, "Play")

    def run_game(self):
        """Основний цикл"""
        while True:
            self._check_events()

            if self.stats.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()

            self._update_screen()

    def _check_events(self):
        """Бінди клавіш"""
        #добавить мишку!!!
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_play_button(self, mouse_pos):
        """Запуск при натиненні кнопки Play"""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:
            # Reset налаштувань
            self.settings.initialize_dynamic_settings()

            # Reset статистики
            self.stats.reset_stats()
            self.stats.game_active = True
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()

            # Видалення прибульців і куль
            self.aliens.empty()
            self.bullets.empty()
            
            # Створення нового флоту та крабля по центру
            self._create_fleet()
            self.ship.center_ship()

            # Прибрати курсор
            pygame.mouse.set_visible(False)

    def _check_keydown_events(self, event):
        """Редагування біндов"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()

    def _check_keyup_events(self, event):
        """Respond to key releases."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _fire_bullet(self):
        """додавання куль до їх масиву"""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_bullets(self):
        """Оновлення положення куль та видалення старих"""
        # Позиція
        self.bullets.update()

        # видалення тих, що зникли
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                 self.bullets.remove(bullet)

        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """Зіткнення куль та кораблів"""
        # видалення елементів після зіткнення
        collisions = pygame.sprite.groupcollide(
                self.bullets, self.aliens, True, True)

        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)
            self.sb.prep_score()
            self.sb.check_high_score()

        if not self.aliens:
            # Знищення куль та створення нового флоту
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            # Підвищення рівня
            self.stats.level += 1
            self.sb.prep_level()

    def _update_aliens(self):
        """Перевірка позицій флоту"""
        self._check_fleet_edges()
        self.aliens.update()

        
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()

        # перевірка чи дійшли до низу екрана
        self._check_aliens_bottom()

    def _check_aliens_bottom(self):
        """Перевірте, чи прибульці досягли нижньої частини екрана."""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                self._ship_hit()
                break

    def _ship_hit(self):
        """Реакція на удар корабля з прибульцем """
        if self.stats.ships_left > 0:
            # Зменшити ships_left і оновити табло.
            self.stats.ships_left -= 1
            self.sb.prep_ships()
            
            # Видаленнябудь-яких прибульців і куль.
            self.aliens.empty()
            self.bullets.empty()
            
            # Новий флот та корабль по центру
            self._create_fleet()
            self.ship.center_ship()
            
            # Пауза
            sleep(0.5)
        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True)

    def _create_fleet(self):
        """Create the fleet of aliens."""
        # Create an alien and find the number of aliens in a row.
        # Spacing between each alien is equal to one alien width.
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        available_space_x = self.settings.screen_width - (2 * alien_width)
        number_aliens_x = available_space_x // (2 * alien_width)
        
        # Визначення кількості рядів інопланетян, які поміщаються на екрані.
        ship_height = self.ship.rect.height
        available_space_y = (self.settings.screen_height -
                                (3 * alien_height) - ship_height)
        number_rows = available_space_y // (2 * alien_height)
        
        # Створення флоту
        for row_number in range(number_rows):
            for alien_number in range(number_aliens_x):
                self._create_alien(alien_number, row_number)

    def _create_alien(self, alien_number, row_number):
        """Створення прибульця та його розміщення в ряду"""
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
        self.aliens.add(alien)

    def _check_fleet_edges(self):
        """Якщо дійшло досягли межі то ..."""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break
            
    def _change_fleet_direction(self):
        """Зміна напрямку флоту"""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _update_screen(self):
        """Оновлення зображення на екрані"""
        self.screen.fill(self.settings.bg_color)
        self.ship.blitme()
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.aliens.draw(self.screen)

        # Табло
        self.sb.show_score()

        # якщо пауза то поява кнопки відновллення
        if not self.stats.game_active:
            self.play_button.draw_button()

        pygame.display.flip()


if __name__ == '__main__':
    # Запуск
    ai = AlienInvasion()
    ai.run_game()
