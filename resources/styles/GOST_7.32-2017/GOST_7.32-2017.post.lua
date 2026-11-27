-- Lua-фильтр pandoc, выполняемый ПОСЛЕ pandoc-crossref (ключ lua_filter_post
-- в config.cfg профиля). Не зависит от конкретного ГОСТа и названий стилей,
-- поэтому его можно подключать из других профилей через относительный путь.
--
-- Задача: оформить заголовок произвольным стилем шаблона. Автор пишет
--
--   ::: {custom-style="StructuralHeading"}
--   # ВВЕДЕНИЕ {-}
--   :::
--
-- DOCX-писатель pandoc всегда назначает заголовку стиль «Heading N», и этот
-- стиль перекрывает custom-style обёртки. Поэтому каждый заголовок внутри
-- Div с custom-style превращается в обычный абзац, который получает стиль
-- обёртки. Всё остальное (выравнивание, начало с новой страницы, уровень
-- структуры для содержания) задаёт сам стиль в reference DOCX.
--
-- Фильтр выполняется после pandoc-crossref, потому что crossref должен
-- увидеть исходные заголовки: по ним он считает главы и берёт буквы
-- приложений из атрибута label. Идентификатор заголовка переносится на
-- обёртку абзаца, и DOCX-писатель сохраняет его как закладку, так что
-- ссылки на заголовок продолжают работать.

local STYLE_KEY = "custom-style"

local function header_to_styled_block(header, style)
    return pandoc.Div(
        { pandoc.Para(header.content) },
        pandoc.Attr(header.identifier, {}, { [STYLE_KEY] = style })
    )
end

return {
    {
        Div = function(div)
            local style = div.attributes[STYLE_KEY]
            if not style or style == "" then
                return nil
            end

            local changed = false
            local blocks = pandoc.Blocks({})
            for _, block in ipairs(div.content) do
                if block.t == "Header" then
                    blocks:insert(header_to_styled_block(block, style))
                    changed = true
                else
                    blocks:insert(block)
                end
            end

            if not changed then
                return nil
            end
            div.content = blocks
            return div
        end,
    },
}
